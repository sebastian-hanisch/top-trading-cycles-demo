"""Jede Zahl in den Hilfetexten, Presets und der README ist hier über die 100 festen Karten (DIST_SEEDS) bzw. die
festen Sweep-/Manipulations-Seedmengen belegt. Alles rechnet mit ganzen Zahlen und einem eigenen Zufallsgenerator -
die Werte sind auf jeder Plattform dieselben; die Toleranzen decken nur die Rundung auf die im Text genannten
Stellen."""

import pytest

import tt_constants as C
import tt_evaluation as ev


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.4f} statt {expected}"


@pytest.fixture(scope="module")
def dist():
    return ev.distribution(20, 0, "noise", 20, C.DIST_SEEDS)


def test_default_map_trade_share(dist):
    near(dist["trade_share_mean"], 0.788, 0.001)
    assert dist["trade_share_median"] == 0.8


def test_default_map_rank_gain(dist):
    near(dist["rank_gain_all"]["mean"], 7.2265, 0.001)
    assert dist["rank_gain_all"]["median"] == 7.0
    near(dist["rank_gain_traders"]["mean"], 9.17, 0.01)
    assert dist["rank_gain_traders"]["median"] == 9.0


def test_default_map_distance_gain(dist):
    near(dist["dist_gain_all"]["mean"], 24.68, 0.01)
    assert dist["dist_gain_all"]["median"] == 21.0
    near(dist["dist_gain_traders"]["mean"], 31.32, 0.01)
    assert dist["dist_gain_traders"]["median"] == 29.0


def test_default_map_cycles_and_effort(dist):
    near(dist["n_cycles"]["mean"], 9.07, 0.01)
    assert dist["n_cycles"]["median"] == 9.0
    near(dist["steps"]["mean"], 106.85, 0.05)
    assert dist["steps"]["median"] == 108.0


def test_cycle_length_distribution(dist):
    assert dist["n_cycles_total"] == 907
    expect = {1: 424, 2: 206, 3: 119, 4: 76, 5: 35, 6: 24, 7: 8, 8: 10, 9: 3, 10: 1, 11: 1}
    assert dist["length_hist"] == expect
    near(dist["length_hist_share"][1], 424 / 907, 1e-9)


def test_length_cap_preview_matches_the_readme_numbers():
    rows = {r["cap"]: r for r in ev.length_cap_preview(20, 0, "noise", 20, C.DIST_SEEDS, C.LENGTH_CAPS)}
    assert rows[1]["lost_dist_share"] == 1.0 and rows[1]["lost_rank_share"] == 1.0
    near(rows[2]["lost_dist_share"], 0.7656, 0.001)
    near(rows[2]["lost_rank_share"], 0.7553, 0.001)
    near(rows[3]["lost_dist_share"], 0.5432, 0.001)
    near(rows[3]["lost_rank_share"], 0.5301, 0.001)
    losses = [rows[c]["lost_dist_share"] for c in C.LENGTH_CAPS]
    assert losses == sorted(losses, reverse=True)


def test_worst_case_ratio_is_pinned_exactly_one():
    rows = {r["n"]: r for r in ev.worst_case_scaling()}
    for n in (10, 20, 40, 80, 160, 320, 640, 1280):
        assert rows[n]["ratio"] == 1.0
        assert rows[n]["steps"] == n * n


def test_effort_scaling_on_the_real_map():
    rows = {r["n"]: r for r in ev.effort_scaling("noise", 20)}
    expect = {10: 39.6, 20: 117.2, 40: 314.6, 80: 804.8, 160: 2668.8, 320: 6355.8, 640: 15647.2}
    for n, steps in expect.items():
        near(rows[n]["steps"], steps, 0.5)
    ns = sorted(expect)
    values = [rows[n]["steps"] for n in ns]
    assert values == sorted(values)                                  # streng wachsend mit n


def test_manipulation_rate_is_zero():
    m = ev.manipulation("noise", 20)
    assert m == {"gain": 0, "total": 200}


def test_individual_rationality_never_violated_at_scale():
    ir = ev.ir_check("noise", 20)
    assert ir == {"violations": 0, "total": 4800}


def test_dead_swap_card_trades_nobody():
    import tt_preferences as P
    import tt_scenario as S
    from tt_ttc import solve
    sc = S.dead_swap_example(20)
    prefs = P.preferences(sc, "dist")
    res = solve(prefs, sc.owner, record=False)
    assert all(s == sc.owner[i] for i, s in res.pairs)


def test_textbook_card_rounds_and_result():
    import tt_scenario as S
    from tt_preferences import preferences
    from tt_ttc import solve
    sc = S.textbook_example()
    res = solve(preferences(sc, "dist"), sc.owner)
    assert res.rounds == 2 and res.cycle_lengths == (3, 2)
    assert [s for _, s in res.pairs] == [1, 2, 0, 4, 3]
