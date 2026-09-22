"""Vorlieben: jede Person ordnet ALLE Plätze (keine Reichweite, keine Seite - ein Rollen-Set, anders als in jedem
bisherigen Matching-Stück). Drei Modelle, alle ganzzahlig und über einen eigenen Zufallsgenerator (SplitMix64) statt
numpy:
- `dist`: nach der Entfernung Ziel i <-> Platz s.
- `noise`: Entfernung + Streuung in [-k, k] Minuten, je Person und Platz unabhängig gezogen. k = 0 ist `dist`.
- `random`: unabhängige Zufallsvorlieben, ohne Bezug zu den Kosten.
Gleichstände werden nach dem Platzindex gebrochen: die Listen sind also STRIKT (tragend für TTC - bei echten
Gleichständen ist TTC nachweislich weder pareto-effizient noch gruppen-anreizkompatibel, siehe README)."""

from tt_scenario import SplitMix64

MASK = (1 << 64) - 1
PREF_LABELS = {"dist": "Nur Entfernung", "noise": "Entfernung mit Streuung", "random": "Zufall"}
DEFAULT_PREF = "noise"
NOISE_MIN, NOISE_MAX, NOISE_STEP, DEFAULT_NOISE = 5, 60, 5, 20


def _draw(seed, i, s, bits):
    """Reproduzierbare Ziehung 0 .. 2^bits - 1 für (Seed, Person, Platz): unabhängig von n."""
    state = seed & MASK
    for part in (i, s):
        state = (state * 1000003 + part + 1) & MASK
    return SplitMix64(state).below(1 << bits)


def _noise(seed, i, s, k):
    return ((2 * k + 1) * _draw(seed, i, s, 20) >> 20) - k


def preferences(sc, model, noise=DEFAULT_NOISE, seed=0):
    """Strikte, VOLLSTÄNDIGE Vorlieben: prefs[i] = alle Plätze, beste zuerst. Karten mit festen Listen liefern diese
    unverändert."""
    if getattr(sc, "lists", None) is not None:
        return [list(x) for x in sc.lists]
    n, c = sc.n, sc.cost
    if model == "dist":
        key = lambda i, s: int(c[i, s])
    elif model == "noise":
        key = lambda i, s: int(c[i, s]) + _noise(seed, i, s, noise)
    elif model == "random":
        key = lambda i, s: _draw(seed, i, s, 30)
    else:
        raise ValueError(model)
    return [sorted(range(n), key=lambda s: (key(i, s), s)) for i in range(n)]


def ranks(lists):
    """Rangtabellen: ranks[a][b] = Platz von b in der Liste von a (0 = beste)."""
    return [{x: k for k, x in enumerate(lst)} for lst in lists]
