"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, Schritt-Zustand, Abspielen (auch auf
mehrbildrigen Karten), Randgrößen, Manipulationsprobe und Aufwand-Sweep auf Abruf, Permalink."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import tt_constants as C
from tt_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def _run(setup=None, timeout=600):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, name):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = C.PRESETS[name][key]


def _set(**kw):
    def setup(at):
        for k, v in kw.items():
            at.session_state[k] = v
    return setup


def _step(at):
    found = [s for s in at.slider if s.key == "tt_step"]
    return found[0] if found else None


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info) + list(at.error)]


def _play(at):
    [b for b in at.button if b.label == "▶️ Abspielen"][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_default_renders_without_exception():
    at = _run()
    assert any("Ablauf" in m.value for m in at.markdown)
    assert not at.error


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders(name):
    at = _run(lambda a: _apply(a, name))
    assert not at.exception


def test_every_preset_step_slider_reaches_the_end():
    for name in C.PRESETS:
        at = _run(lambda a: _apply(a, name))
        step = _step(at)
        if step is not None:
            assert step.value == step.max


def test_play_runs_through_all_frames_on_a_multi_event_map():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    assert _step(at).max > 10
    _play(at)


def test_play_on_a_fixed_card():
    at = _run(lambda a: _apply(a, "📖 Lehrbuchkarte (zwei Runden)"))
    if _step(at).max > 0:
        _play(at)


def test_step_slider_visits_every_kind_of_event():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    last = int(_step(at).max)
    for k in (0, 1, last // 3, last // 2, last - 1, last):
        _step(at).set_value(k)
        at.run()
        assert not at.exception, (k, [e.value for e in at.exception])


def test_extreme_sizes_render():
    for n in (C.N_MIN, C.N_MAX):
        at = _run(_set(n_slider=n))
        assert not at.exception


def test_fixed_card_hides_random_controls():
    at = _run(_set(card_select=C.CARD_TEXTBOOK))
    labels = {s.label for s in at.sidebar.slider}
    assert labels == set()
    at2 = _run(_set(card_select=C.CARD_NONE))
    labels2 = {s.label for s in at2.sidebar.slider}
    assert "Personen" in labels2 and "Ballung [%]" in labels2


def test_noise_slider_hidden_unless_pref_is_noise():
    at = _run(_set(pref_radio="dist"))
    assert "Streuung [min]" not in {s.label for s in at.sidebar.slider}
    at = _run(_set(pref_radio="noise"))
    assert "Streuung [min]" in {s.label for s in at.sidebar.slider}


def test_step_slider_returns_to_the_last_step_when_the_map_changes():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    last = int(_step(at).max)
    assert _step(at).value == last
    _step(at).set_value(2)
    at.run()
    assert _step(at).value == 2
    at.session_state["seed_input"] = C.PRESETS["🗺️ Mittlere Karte"]["seed"] + 1
    at.run()
    assert _step(at).value == _step(at).max


def test_solved_end_state_shows_the_certificate():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    at.session_state["tt_step"] = int(_step(at).max)
    at.run()
    proof = next((t.value for t in at.table if "Bestandteil" in t.value.to_dict("list")), None)
    assert proof is not None


def test_experiments_run_on_demand():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    for key in ("manip_start", "scale_start"):
        at.button(key=key).click()
        at.run()
        assert not at.exception, [e.value for e in at.exception]


def test_permalink_roundtrip_and_clamping():
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.query_params["n"] = "999999"
    at.query_params["pref"] = "not-a-real-model"
    at.run()
    assert not at.exception
    n_slider = at.sidebar.slider(key="n_slider")
    assert n_slider.value == C.N_MAX


def test_no_dead_file_links_in_markdown():
    at = _run()
    texts = " ".join(m.value for m in at.markdown)
    assert "tt_ttc.py)" not in texts and "app.py)" not in texts


def test_footer_present():
    at = _run()
    assert any("sebastianhanisch.net" in c.value for c in at.caption)


def test_length_cap_preview_section_renders_on_random_card():
    at = _run(lambda a: _apply(a, "🗺️ Mittlere Karte"))
    texts = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "Höchstlänge" in texts or "kurze Kreise" in texts
