"""Top Trading Cycles - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Dritte Erweiterung des Gale-Shapley-Asts der Matching-Linie, aber strukturell ein echter Bruch: kein
Deferred-Acceptance-Verwandter. Gales Algorithmus (Shapley & Scarf 1974) löst den Wohnungsmarkt: jeder besitzt schon
genau ein Gut und hat eine VOLLSTÄNDIGE Präferenz über alle Güter. Der direkte algorithmische Unterbau für
Nierentausch (nächstes und letztes geplantes Stück). Siehe README.

Lauffähig mit: streamlit run app.py
"""

import time

import numpy as np
import streamlit as st

import tt_constants as C
import tt_evaluation as ev
from tt_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from tt_ttc import EV_ADVANCE, EV_CYCLE, EV_POINT
from tt_visualization import build_cap_preview, build_length_hist, build_map, build_progress, build_scale

st.set_page_config(page_title="Top Trading Cycles – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _ms(s, digits=1):
    return "–" if s["mean"] is None else f"{_f(s['mean'], digits)} | {_f(s['median'], digits)}"


def _share(x):
    return "–" if x is None else f"{100 * x:.0f} %"


@st.cache_resource(show_spinner=False, max_entries=16)
def _analysis(params):
    card, pref, noise, n, ballung, seed = params
    sc = ev.scenario_from_settings(card, n, ballung, seed)
    return ev.analyse(sc, pref, noise, seed)


@st.cache_data(show_spinner=False)
def _distribution(n, ballung, pref, noise):
    return ev.distribution(n, ballung, pref, noise)


@st.cache_data(show_spinner=False)
def _length_cap_preview(n, ballung, pref, noise):
    return ev.length_cap_preview(n, ballung, pref, noise)


@st.cache_data(show_spinner=False)
def _effort_scaling(pref, noise):
    return ev.effort_scaling(pref, noise)


@st.cache_data(show_spinner=False)
def _worst_case_scaling():
    return ev.worst_case_scaling()


@st.cache_data(show_spinner=False)
def _manipulation(pref, noise):
    return ev.manipulation(pref, noise)


@st.cache_data(show_spinner=False)
def _ir_check(pref, noise):
    return ev.ir_check(pref, noise)


st.title("🅿️ Top Trading Cycles – Tausch ohne Geld")
st.markdown(
    """
**Gale-Shapley und Krankenhaus-Zulassung** paaren Bewerber mit Anbietern. Hier besitzt **jeder schon etwas** und
tauscht direkt: n Beschäftigte besitzen bereits einen festen Dauerparkplatz, jeder ordnet ALLE Plätze nach Entfernung
zum eigenen Ziel. **Top Trading Cycles** (Gale, in Shapley & Scarf 1974) findet die eindeutige, **kernstabile**
Zuordnung - und ist gleichzeitig der einzige Mechanismus, der Pareto-effizient, individuell-rational UND
strategiefest zugleich ist (Ma 1994).
"""
)
st.caption(
    "Drittes von vier neuen Stücken der Matching-Linie (nach Stabile Mitbewohner und Krankenhaus-Zulassung), "
    "inspiriert von Alvin Roths Marktdesign-Arbeiten. Der direkte algorithmische Unterbau für das nächste, letzte Stück: Nierentausch."
)

with st.expander("So funktioniert Top Trading Cycles", expanded=True):
    st.markdown(
        """
1. **Jeder zeigt auf seinen Favoriten:** jede noch aktive Person zeigt auf die aktuelle Besitzerin ihres besten noch
   verfügbaren Platzes (das kann der eigene sein - dann eine Selbstschleife).
2. **Mindestens ein Kreis existiert immer:** da jede Person auf genau eine andere zeigt, muss die Verfolgung
   irgendwann einen bereits besuchten Knoten erneut treffen.
3. **Kreis auflösen:** jede Person im Kreis bekommt den Platz, auf den sie zeigt, und verlässt mit ihm den Markt - für
   immer, nicht nur ihr Zielpunkt ändert sich, sondern auch der Platz ist ab jetzt vergeben.
4. **Wiederholen**, bis niemand mehr übrig ist. Terminiert immer (in jeder Runde verlässt mindestens eine Person).
        """
    )

st.caption("🎯 Schnellstart – eine Beispielkarte laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    card = st.session_state.get("card_select", C.CARD_NONE)
    if card == C.CARD_NONE:
        pref = st.radio("Vorlieben", list(C.PREF_LABELS), key="pref_radio", format_func=lambda k: C.PREF_LABELS[k])
        noise = st.slider("Streuung [min]", *bounds("noise_slider"), key="noise_slider", step=C.NOISE_STEP) if pref == "noise" else C.DEFAULT_NOISE
        n = st.slider("Personen", *bounds("n_slider"), key="n_slider")
        ballung = st.slider("Ballung [%]", *bounds("ballung_slider"), key="ballung_slider", step=25)
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
        st.button("🎲 Neue Karte generieren", width="stretch", on_click=randomize_seed)
    else:
        pref, noise, ballung, seed = st.session_state.get("pref_radio", C.DEFAULT_PREF), C.DEFAULT_NOISE, C.DEFAULT_BALLUNG, st.session_state.get("seed_input", C.DEFAULT_SEED)
        n = st.session_state.get("n_slider", C.DEFAULT_N)
        st.caption(f"Feste Karte ({C.CARD_LABELS[card]}) - es gibt nichts zu erzeugen.")

# --- Ablauf --------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ablauf")
step_col, play_col = st.columns([6, 2])
params = (card, pref, int(noise), int(n), int(ballung), int(seed))
with st.spinner("Rechne..."):
    a = _analysis(params)
sc, res, prefs = a.scenario, a.result, a.prefs
d = ev.verdict(a)
n_events = res.n_events
if st.session_state.get("tt_step_owner") != params:
    st.session_state["tt_step"] = n_events
    st.session_state["tt_step_owner"] = params
with step_col:
    if n_events > 0:
        step = st.slider("Ereignis", 0, n_events, key="tt_step")
    else:
        step = 0
        st.caption("Kein Ereignis: keine Personen.")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=n_events == 0)
sync_query_params({"card_select": card, "pref_radio": pref, "noise_slider": int(noise), "n_slider": int(n), "ballung_slider": int(ballung), "seed_input": int(seed)})
view_slot = st.empty()


def _event_text(k):
    if k == 0:
        return f"Anfang: alle {sc.n} Personen sind aktiv, jede besitzt ihren Ausgangsplatz. Noch kein Zeiger gesetzt."
    e = res.events[k - 1]
    if e.kind == EV_ADVANCE:
        return f"Person {e.person}: Platz {e.slot} ist nicht mehr verfügbar (Besitzerin bereits ausgeschieden) - Zeiger rückt vor."
    if e.kind == EV_POINT:
        return f"Person {e.person} zeigt auf Platz {e.slot} (aktuelle Besitzerin: Person {e.owner})."
    if e.kind == EV_CYCLE:
        return f"Kreis gefunden: {' → '.join(str(p) for p in e.cycle)} → {e.cycle[0]}. Jede erhält den Platz, auf den sie zeigt, und verlässt den Markt."
    return "unbekanntes Ereignis"


def _cert_table():
    c = a.cert
    ok = lambda b: "✅" if b else "❌"
    rows = [("Gültige Zuordnung", ok(c["s1_valid"])), ("Individuelle Rationalität", ok(c["s2_individually_rational"])), ("Kein blockierendes Tauschpaar", ok(c["s3_no_pair_swap"]))]
    return {"Bestandteil": [r[0] for r in rows], "Ergebnis": [r[1] for r in rows]}


def _render(k):
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**Nach {k} von {n_events} Ereignissen** – " + _event_text(k))
        c1.plotly_chart(build_map(sc, prefs, res, k), width="stretch", key=f"tt_map_{k}")
        c2.markdown("**Verlauf**")
        c2.plotly_chart(build_progress(res, k), width="stretch", key=f"tt_progress_{k}")
        if k == n_events:
            st.markdown("**Beweis:** notwendige Bedingungen für Kern-Stabilität (die vollständige, erschöpfende Prüfung über alle Koalitionsgrößen macht `tt_oracle.py` in den Tests).")
            st.table(_cert_table())


if auto_play:
    frames = sorted({int(round(x)) for x in np.linspace(0, n_events, min(n_events, 40) + 1)})
    for k in frames:
        _render(k)
        time.sleep(min(0.6, 6.0 / max(len(frames), 1)))
    step = n_events
else:
    _render(step)

st.caption("Kreise: Zielpunkte der Personen (offen = noch aktiv, gefüllt = hat getauscht und verlassen). Quadrate: Plätze. "
           "Gepunktete graue Linie: aktueller Zeiger. Dicke grüne Linie: abgeschlossener Tausch. Lila: der zuletzt gefundene Kreis.")

st.markdown("---")

# --- Wer tauscht, wie viele Kreise? ---------------------------------------------------------------------------------

st.markdown("## 🎯 Wer tauscht, und wie viel bringt es?")
st.success(f"✅ {d['n_traders']} von {d['n']} Personen tauschen ({_share(d['trade_share'])}), in {d['n_cycles']} Kreisen (Längen {', '.join(str(x) for x in d['cycle_lengths'])}) - "
           f"{'Zertifikat bestätigt' if d['cert']['all_ok'] else 'Zertifikat NICHT bestätigt'}.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tauschanteil", _share(d["trade_share"]))
m2.metric("Rang-Verbesserung (Tauschende)", _ms(d["rank_gain_traders"], 1))
m3.metric("Distanzgewinn (Tauschende)", _ms(d["dist_gain_traders"], 1))
m4.metric("Aufwand (Schritte)", _f(d["steps"], 0))

st.markdown(f"**Nicht nur diese eine Karte:** {len(C.DIST_SEEDS)} feste Karten mit denselben Einstellungen (Personen {n}, Ballung {ballung} %), getrennt vom Seed oben.")
if card == C.CARD_NONE:
    dist = _distribution(int(n), int(ballung), pref, int(noise))
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Tauschanteil (Mittel | Median)", f"{_share(dist['trade_share_mean'])} | {_share(dist['trade_share_median'])}")
    p2.metric("Rang-Verbesserung, alle (Mittel | Median)", _ms(dist["rank_gain_all"]))
    p3.metric("Kreise je Karte (Mittel | Median)", _ms(dist["n_cycles"], 1))
    p4.metric("Aufwand (Mittel | Median)", _ms(dist["steps"], 0))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_length_hist(dist["length_hist_share"]), width="stretch", key="tt_hist_chart")
    c2.table({"Länge": list(dist["length_hist"]), "Anzahl": list(dist["length_hist"].values()), "Anteil": [_share(dist["length_hist_share"][L]) for L in dist["length_hist"]]})
else:
    st.info("Feste Karte: es gibt nur diese eine Ziehung. Für die Verteilung über viele Karten eine zufällige Karte wählen.")

st.markdown("---")

# --- Überleitung zu Nierentausch -------------------------------------------------------------------------------------

st.subheader("🔬 Was, wenn nur kurze Kreise erlaubt wären?")
st.caption("STRUKTURELLE Vorschau, keine neu berechnete Mechanik: TTCs eigenes, unbeschränktes Ergebnis nachträglich gefiltert (Kreise über der Höchstlänge werden verworfen, ihre Mitglieder behalten ihren Ausgangsplatz). Keine Nierentausch-Zahl - nur die Motivation dafür.")
if card == C.CARD_NONE:
    lc = _length_cap_preview(int(n), int(ballung), pref, int(noise))
    st.plotly_chart(build_cap_preview(lc), width="stretch", key="tt_cap_chart")
    st.caption(f"Bei Höchstlänge 2 gingen {_share(lc[1]['lost_dist_share'])} des Distanzgewinns verloren, bei Höchstlänge 3 noch {_share(lc[2]['lost_dist_share'])} - "
               "lange Kreise tragen überproportional viel bei. Nierentausch ist real meist auf kurze Zyklen (Simultan-OPs) oder Ketten (altruistische Spender) beschränkt.")
else:
    st.info("Feste Karte: für die Vorschau eine zufällige Karte wählen.")

st.markdown("---")

st.subheader("🔬 Lohnt sich Lügen?")
if st.button("Manipulationsprobe rechnen (5×5-Karten, alle Meldungen)", key="manip_start"):
    st.session_state["manip_on"] = True
if st.session_state.get("manip_on"):
    with st.spinner("Rechne erschöpfend über alle Permutationen..."):
        m = _manipulation(pref, int(noise))
    st.table({"Wer": ["Person (Präferenzliste)"], "Gewinnt durch Lüge": [f"{m['gain']} von {m['total']}"]})
    st.caption("Niemand gewinnt (Theorem, hier erschöpfend bestätigt): Top Trading Cycles ist der Kern-Mechanismus, und der Kern-Mechanismus ist strategiefest (Roth 1982).")

st.markdown("---")

st.subheader("🔬 Wovon hängt der Aufwand ab?")
if st.button("Aufwand gegen die Größe (n = 10 bis 640/1280)", key="scale_start"):
    st.session_state["scale_on"] = True
if st.session_state.get("scale_on"):
    with st.spinner("Rechne..."):
        srows, wrows = _effort_scaling(pref, int(noise)), _worst_case_scaling()
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_scale(srows, wrows), width="stretch", key="tt_scale_chart")
    c2.table({"n": [r["n"] for r in wrows], "Schritte/n² (Worst Case)": [_f(r["ratio"], 4) for r in wrows]})
    st.caption("Worst Case (identische Präferenzliste, Identitätsbesitz): Schritte/n² = 1,0000 exakt - ein bewiesener Θ(n²)-Fall. Auf der echten geometrischen Karte liegt der gemessene Aufwand klar darunter (empirisch, kein Beweis).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Vollständige Präferenzen** (kein Erreichbarkeits-Cutoff) | Reale Tauschbörsen kennen oft nur einen Teil der möglichen Partner. | (außerhalb der Linie) |
| **Strikte Präferenzen** | Bei echten Gleichständen ist TTC weder pareto-effizient noch gruppen-anreizkompatibel. | (außerhalb der Linie) |
| **Freier Tausch, keine Kompatibilitäts-/Kurzzyklus-Zwänge** | Nierenspenden brauchen medizinische Kompatibilität UND kurze Zyklen (Simultan-OPs) oder Ketten (altruistische Spender). | **Nierentausch** (geplant, letztes Stück) |
"""
)
st.caption("Damit bleibt in der erweiterten Matching-Linie noch Nierentausch offen.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell (Wohnungsmarkt, Shapley & Scarf 1974).** Personen $N = \{1, ..., n\}$, jede besitzt ein Gut $\omega_i$
(Permutation von $N$ auf sich selbst). Jede Person hat eine strikte, vollständige Präferenz $\succ_i$ über alle
Güter. Gesucht: eine Zuordnung $\mu$ (Permutation), die im **Kern** liegt - keine Koalition $S \subseteq N$ kann durch
internen Neu-Tausch NUR ihrer eigenen Ausgangsgüter alle Mitglieder mindestens so gut und mindestens eines strikt
besser stellen.

**Top Trading Cycles (Gale).** Jede aktive Person zeigt auf die aktuelle Besitzerin ihres besten verbleibenden Guts
(ggf. sich selbst). Da jeder Knoten Außengrad 1 hat, existiert mindestens ein Kreis; jede Person im Kreis bekommt das
Gut, auf das sie zeigt, und verlässt den Markt. Terminiert immer in höchstens $n$ Runden.

**Kern-Eindeutigkeit (Roth & Postlewaite 1977, JME).** Bei strikten Präferenzen ist der Kern eines Wohnungsmarkts
NIE leer (Shapley & Scarf 1974) und besteht aus GENAU EINER Zuordnung - der TTC-Zuordnung. TTC = der einzige Kern =
die einzige walrasianische (Wettbewerbs-)Allokation.

**Strategiefestigkeit (Roth 1982, Economics Letters).** Der Kern-Mechanismus (= TTC) ist strategiefest: kein
Teilnehmer kann sich durch eine falsche Präferenzangabe verbessern.

**Eindeutigkeitssatz (Ma 1994, International Journal of Game Theory).** TTC ist der EINZIGE Mechanismus, der
gleichzeitig Pareto-effizient, individuell-rational UND strategiefest ist. (Nicht Roth 1982 - der zeigt nur, dass der
Kern-Mechanismus selbst diese Eigenschaft hat, nicht dass er der einzige mit dieser Kombination ist.)

**Komplexität.** Θ(n²) im schlechtesten Fall (eigene Messung: Schritte/n² = 1,0000 exakt für n = 10 bis 1280 an der
Worst-Case-Karte mit identischer Präferenzliste). Diese Aussage ist von der auf der echten geometrischen Karte
GEMESSENEN, deutlich niedrigeren Wachstumsrate zu unterscheiden (empirisch, kein Beweis für den allgemeinen Fall).

Implementiert in `tt_scenario.py` (Karte, unabhängige Anfangsbesitz-Permutation), `tt_preferences.py`, `tt_ttc.py`
(Kern mit Ereignisprotokoll und Zertifikat), `tt_oracle.py` (Brute Force über alle Koalitionen), `tt_strategy.py`
(Manipulationsprobe).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
