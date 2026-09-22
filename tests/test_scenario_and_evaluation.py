"""Szenario- und Auswertungsmodule: Struktur, Konsistenz, feste Karten."""

import numpy as np

import tt_constants as C
import tt_evaluation as ev
import tt_preferences as P
import tt_scenario as S


def test_from_points_cost_matches_travel_cost():
    sc = S.from_points([(0, 0), (10, 0)], [(0, 0), (0, 5)], owner=(0, 1))
    assert sc.cost[0, 0] == 0 and sc.cost[0, 1] == 5 and sc.cost[1, 0] == 10


def test_owner_is_a_permutation():
    for sd in C.DIST_SEEDS[:20]:
        sc = S.generate(20, 0, sd)
        assert sorted(sc.owner) == list(range(20))


def test_owner_stream_is_independent_of_point_stream():
    """Zwei Karten mit gleichem Seed, aber die eine mit XOR-Konstante 0 statt der echten `OWNER_STREAM_XOR`, sollten
    NICHT denselben Anfangsbesitz haben (sonst waere der Strom nicht wirklich unabhaengig von etwas anderem als dem
    Seed selbst) - eine Absicherung gegen ein versehentliches Zusammenlegen der beiden Stroeme."""
    sc = S.generate(20, 0, 12345)
    rng_default = S.SplitMix64(12345 ^ S.OWNER_STREAM_XOR)
    rng_alt = S.SplitMix64(12345)
    owner_default = S._shuffle(20, rng_default)
    owner_alt = S._shuffle(20, rng_alt)
    assert tuple(owner_default) == sc.owner
    assert tuple(owner_alt) != sc.owner


def test_preferences_are_complete_and_strict():
    sc = S.generate(15, 0, 55)
    for model in ("dist", "noise", "random"):
        prefs = P.preferences(sc, model, 20, 55)
        for p in prefs:
            assert sorted(p) == list(range(15))                 # vollstaendig, jede Person ordnet ALLE Plaetze


def test_preferences_are_reproducible():
    sc = S.generate(15, 0, 55)
    p1 = P.preferences(sc, "noise", 20, 55)
    p2 = P.preferences(sc, "noise", 20, 55)
    assert p1 == p2


def test_fixed_cards_have_lists_set_and_ignore_pref_model():
    for card_fn in (S.textbook_example, lambda: S.worst_case(10)):
        sc = card_fn()
        assert sc.lists is not None
        for model in ("dist", "noise", "random"):
            assert P.preferences(sc, model) == [list(x) for x in sc.lists]


def test_analyse_and_verdict_roundtrip():
    sc = S.generate(20, 0, C.DEFAULT_SEED)
    a = ev.analyse(sc, "noise", 20, C.DEFAULT_SEED)
    d = ev.verdict(a)
    assert d["n"] == 20
    assert 0 <= d["n_traders"] <= 20
    assert d["cert"]["all_ok"]


def test_distribution_shape():
    d = ev.distribution(10, 0, "noise", 20, C.DIST_SEEDS[:20])
    assert d["n_seeds"] == 20
    assert 0 <= d["trade_share_mean"] <= 1
    assert sum(d["length_hist"].values()) == d["n_cycles_total"]
    assert abs(sum(d["length_hist_share"].values()) - 1.0) < 1e-9


def test_length_cap_preview_is_monotonic_and_bounded():
    rows = ev.length_cap_preview(20, 0, "noise", 20, C.DIST_SEEDS[:30], (1, 2, 3, 4))
    losses = [r["lost_dist_share"] for r in rows]
    assert losses == sorted(losses, reverse=True)                # groesseres Cap verliert nie mehr
    assert all(0.0 <= x <= 1.0 for x in losses)
    assert rows[0]["cap"] == 1 and rows[0]["lost_dist_share"] == 1.0   # Cap 1 = nur Selbstschleifen = aller Gewinn weg (falls jemand mit Laenge > 1 tauscht)


def test_effort_scaling_grows_roughly_with_n():
    rows = ev.effort_scaling("noise", 20, (10, 40, 160), C.DIST_SEEDS[:5])
    steps = [r["steps"] for r in rows]
    assert steps == sorted(steps)                                 # mehr Personen -> nie weniger Aufwand im Mittel


def test_worst_case_scaling_ratio_is_pinned_at_one():
    rows = ev.worst_case_scaling((10, 100, 1000))
    for r in rows:
        assert r["ratio"] == 1.0


def test_manipulation_and_ir_are_cached_and_zero():
    m = ev.manipulation("noise", 20, 5, C.DIST_SEEDS[:10])
    assert m["gain"] == 0 and m["total"] == 50
    ir = ev.ir_check("noise", 20, (5,), C.DIST_SEEDS[:10])
    assert ir["violations"] == 0 and ir["total"] == 50
