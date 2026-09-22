"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Top Trading Cycles"."""

N_MIN, N_MAX, DEFAULT_N = 3, 40, 20
BALLUNG_MIN, BALLUNG_MAX, DEFAULT_BALLUNG = 0, 100, 0   # ganze Prozent, Schritt 25
DEFAULT_SEED = 97
SEED_MAX = 2_000_000_000

CARD_NONE = "none"
CARD_TEXTBOOK = "textbook"
CARD_WORST = "worst_case"
CARD_DEAD = "dead_swap"
CARDS = {CARD_NONE: "Zufällige Karte", CARD_TEXTBOOK: "Lehrbuchkarte (n=5, zwei Runden)", CARD_WORST: "Worst Case Θ(n²)", CARD_DEAD: "Negativbeispiel: kaum jemand tauscht"}
CARD_LABELS = CARDS
DEFAULT_CARD = CARD_NONE

PREF_LABELS = {"dist": "Nur Entfernung", "noise": "Entfernung mit Streuung", "random": "Zufall"}
DEFAULT_PREF = "noise"
NOISE_MIN, NOISE_MAX, NOISE_STEP, DEFAULT_NOISE = 5, 60, 5, 20

# --- feste Seed-Mengen (dieselben wie in den Vorgängerdemos; unabhängig vom Nutzer-Seed) ---------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
SIZE_SEEDS = DIST_SEEDS[:40]
NOISE_SWEEP = (0, 5, 10, 20, 30, 40, 60)
EFFORT_NS = (10, 20, 40, 80, 160, 320, 640)
EFFORT_SEEDS = DIST_SEEDS[:5]
MANIP_SEEDS = DIST_SEEDS[:40]
MANIP_SIZE = 5
LENGTH_CAPS = (1, 2, 3, 4)
ORACLE_SEEDS = DIST_SEEDS[:60]

COLORS = {"self": "#1f77b4", "cycle": "#2ca02c", "point": "#ff7f0e", "advance": "#d62728", "slot": "#111111", "target": "#9467bd"}

# --- Presets --------------------------------------------------------------------------------------------------------
_BASE = dict(card=CARD_NONE, pref=DEFAULT_PREF, noise=DEFAULT_NOISE, n=DEFAULT_N, ballung=DEFAULT_BALLUNG, seed=DEFAULT_SEED)
PRESETS = {
    "📖 Lehrbuchkarte (zwei Runden)": {**_BASE, "card": CARD_TEXTBOOK},
    "🐌 Worst Case Θ(n²)": {**_BASE, "card": CARD_WORST, "n": 20},
    "🗺️ Mittlere Karte": {**_BASE},
    "🎲 Reichlich Rauschen": {**_BASE, "noise": 60, "seed": 41},
    "📏 Nur Entfernung": {**_BASE, "pref": "dist", "seed": 21},
    "🎯 Kleine Gruppe, ein langer Kreis": {**_BASE, "n": 6, "pref": "random", "seed": 47},
    "😴 Kaum jemand tauscht": {**_BASE, "card": CARD_DEAD, "n": 20, "pref": "dist"},
    "🔬 Beweis": {**_BASE, "n": 7, "pref": "random", "seed": 5},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py über die 100 festen Karten (DIST_SEEDS) belegt
PRESET_HELP = {
    "📖 Lehrbuchkarte (zwei Runden)": "Von Hand nachvollzogene Karte (n=5): Runde 1 ein 3er-Kreis (0→1→2→0), Runde 2 ein 2er-Kreis (3,4). Jeder verbessert sich um genau 1 Rangplatz.",
    "🐌 Worst Case Θ(n²)": "Alle Teilnehmer haben dieselbe Präferenzliste, Anfangsbesitz = Identität: jede Runde löst genau eine Selbstschleife auf, macht n Runden nötig - der bewiesene Θ(n²)-Worst-Case (Schritte/n² = 1,0000 exakt, unabhängig von n).",
    "🗺️ Mittlere Karte": "Realistische Einstellungen: im Mittel 78,8 % tauschen tatsächlich (Median 80 %), im Mittel 9,1 Kreise je Karte (100 feste Karten).",
    "🎲 Reichlich Rauschen": "Starkes Rauschen nähert sich Zufallsvorlieben an: auf dieser Karte tauschen alle 20, in 5 Kreisen (Längen 2 bis 9).",
    "📏 Nur Entfernung": "Alle Teilnehmer ordnen streng nach Entfernung: 15 von 20 tauschen, in bis zu 10 Kreisen gleichzeitig (Länge 1 bis 5).",
    "🎯 Kleine Gruppe, ein langer Kreis": "6 Teilnehmer, Zufallsvorlieben: ein einziger 5er-Kreis fasst fünf der sechs, nur einer behält seinen Platz - Kreise können auch bei kleinen Gruppen fast alle erfassen.",
    "😴 Kaum jemand tauscht": "Negativbeispiel, bewusst gezeigt (keine versteckte Modellierungsfalle): Platz s liegt hier exakt auf Zielpunkt s - der eigene Platz ist für JEDEN die beste Wahl, 0 von 20 tauschen. Zeigt, warum `tt_scenario.py`s unabhängige Anfangsbesitz-Permutation für jede andere Karte tragend ist.",
    "🔬 Beweis": "Kleine Karte (n=7, 4 von 7 tauschen): klein genug, dass `tt_oracle.py` Kern-Stabilität, individuelle Rationalität und Pareto-Effizienz erschöpfend nachprüfen kann (in den Tests, nicht live in der App).",
}
