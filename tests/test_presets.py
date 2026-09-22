"""Presets: jedes hat einen Hilfetext, die genannten Zahlen stimmen, Regler-/Schrittgitter sind gültig."""

import tt_constants as C
import tt_evaluation as ev
from tt_presets import PRESET_KEYS, SETTING_SPECS, STEPS


def test_every_preset_has_help_text():
    for name in C.PRESETS:
        assert name in C.PRESET_HELP and C.PRESET_HELP[name]


def test_preset_keys_cover_every_setting_spec():
    assert set(PRESET_KEYS.values()) == set(SETTING_SPECS)
    for name, p in C.PRESETS.items():
        assert set(p) == set(PRESET_KEYS), name


def test_bounds_and_step_grid_are_valid():
    for state_key, spec in SETTING_SPECS.items():
        if spec.lo is not None and spec.hi is not None and isinstance(spec.default, (int, float)):
            assert spec.lo <= spec.default <= spec.hi, state_key
    for key, step in STEPS.items():
        lo, hi = SETTING_SPECS[key].lo, SETTING_SPECS[key].hi
        assert (hi - lo) % step == 0, key


def test_presets_do_not_collide_with_dist_seeds():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def _verdict_for(name):
    p = C.PRESETS[name]
    sc = ev.scenario_from_settings(p["card"], p["n"], p["ballung"], p["seed"])
    a = ev.analyse(sc, p["pref"], p["noise"], p["seed"])
    return ev.verdict(a)


def test_presets_show_what_the_help_text_says():
    d = _verdict_for("📖 Lehrbuchkarte (zwei Runden)")
    assert d["cycle_lengths"] == (3, 2)

    d = _verdict_for("🐌 Worst Case Θ(n²)")
    assert d["cycle_lengths"] == tuple([1] * 20)

    d = _verdict_for("😴 Kaum jemand tauscht")
    assert d["n_traders"] == 0

    d = _verdict_for("🎯 Kleine Gruppe, ein langer Kreis")
    assert max(d["cycle_lengths"]) == 5

    d = _verdict_for("📏 Nur Entfernung")
    assert d["n_traders"] == 15

    d = _verdict_for("🎲 Reichlich Rauschen")
    assert d["n_traders"] == 20

    d = _verdict_for("🔬 Beweis")
    assert d["n_traders"] == 4


def test_default_preset_matches_test_claims():
    """20/Ballung 0/noise 20/Seed 97 ist zugleich der Standard UND die Basis von tests/test_claims.py."""
    sc = ev.scenario_from_settings(C.CARD_NONE, C.DEFAULT_N, C.DEFAULT_BALLUNG, C.DEFAULT_SEED)
    a = ev.analyse(sc, C.DEFAULT_PREF, C.DEFAULT_NOISE, C.DEFAULT_SEED)
    d = ev.verdict(a)
    assert d["cert"]["all_ok"]
    assert d["n"] == 20


def test_proof_preset_is_small_enough_for_the_oracle():
    """Das 'Beweis'-Preset muss innerhalb von tt_oracle.PRACTICAL_MAX_N liegen."""
    import tt_oracle as O
    assert C.PRESETS["🔬 Beweis"]["n"] <= O.PRACTICAL_MAX_N
