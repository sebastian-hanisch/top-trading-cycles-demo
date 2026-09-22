"""Szenario: Dauerparkplatz-Tausch. n Beschäftigte, jeder besitzt bereits einen fest zugewiesenen Parkplatz (lange her
vergeben, nicht an den heutigen Zielpunkt gekoppelt). Jeder ordnet ALLE Plätze nach Entfernung zum eigenen Zielpunkt -
anders als in jedem bisherigen Stück der Matching-Linie gibt es hier KEINE Reichweite/Erreichbarkeits-Schranke: es ist
dieselbe Tiefgarage, jeder Platz ist für jeden erreichbar, die Listen sind also immer vollständig.

Alles ist ganzzahlig und läuft über einen eigenen Zufallsgenerator (SplitMix64 auf Python-Ints) statt über
`numpy.random`: numpy garantiert keine über Versionen stabilen Zufallsströme, die CI installiert aber wöchentlich die
neueste Version. So sind Voreinstellungen, Seeds und jede im Text genannte Zahl auf Windows und Linux dieselben.
Kosten = auf ganze Minuten aufgerundete Entfernung (per `isqrt`, ohne Gleitkomma).

**Kritisch:** der Anfangsbesitz (wer welchen Platz schon hat) ist eine vom Zielpunkt-Punktesatz UNABHÄNGIGE
Zufallspermutation, aus einem eigenen `SplitMix64`-Strom (analog `hr_scenario.py`s Kapazitätsvergabe). Würde der
Anfangsbesitz stattdessen z. B. mit dem Index oder derselben Ziehung wie die Zielpunkte zusammenhängen, wäre der
eigene Platz für fast jeden trivial die beste Wahl (kürzeste Distanz zu sich selbst) - dann besteht TTC fast nur aus
Selbstschleifen und die Demo zeigt inhaltlich nichts, obwohl alle Tests bestünden. Siehe `hofstellplatz-demo`
(Negativbeispiel-Lehre in einer anderen Linie) für dieselbe Fehlerklasse."""

from dataclasses import dataclass
from math import isqrt

import numpy as np

_MASK = (1 << 64) - 1
MAP_SIZE = 100
N_CENTRES = 3
OWNER_STREAM_XOR = 0x546F70546F70544D   # eigener, von der Punktziehung unabhaengiger Strom fuers Anfangseigentum


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def below(self, n):
        """Ganzzahl in 0..n-1 (die Modulo-Verzerrung bei n <= 101 liegt um 1e-17)."""
        return self.next() % n


def travel_cost(dx, dy):
    """Aufgerundete Entfernung in Minuten und das Quadrat der Entfernung (beides ganzzahlig)."""
    d2 = dx * dx + dy * dy
    r = isqrt(d2)
    return r + (1 if d2 > r * r else 0), d2


def _shuffle(n, rng):
    """Fisher-Yates, reine Ganzzahl-Arithmetik (wie `hr_scenario._capacities`s Gewichtsziehung)."""
    perm = list(range(n))
    for i in range(n - 1, 0, -1):
        j = rng.below(i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


@dataclass(frozen=True)
class Scenario:
    targets: tuple    # ((x, y), ...) Zielpunkt je Beschäftigtem i
    slots: tuple       # ((x, y), ...) Position von Platz s
    owner: tuple        # owner[i] = Platz, den i zu Beginn besitzt (Permutation von 0..n-1)
    cost: np.ndarray    # (n, n) int64, Entfernung Ziel i <-> Platz s in Minuten
    lists: tuple = None  # feste Vorlieben (eine Liste je Person) bei den Lehrbuchkarten; sonst None (aus tt_preferences)

    @property
    def n(self):
        return len(self.targets)


def from_points(targets, slots, owner, lists=None):
    n = len(targets)
    cost = np.zeros((n, n), dtype=np.int64)
    for i, (tx, ty) in enumerate(targets):
        for s, (sx, sy) in enumerate(slots):
            c, _ = travel_cost(tx - sx, ty - sy)
            cost[i, s] = c
    return Scenario(tuple(map(tuple, targets)), tuple(map(tuple, slots)), tuple(owner), cost, lists)


def generate(n, ballung, seed):
    """Zufällige Karte. `ballung` in ganzen Prozent: 0 = gleichmäßig verteilt, 100 = alle Punkte um drei Zentren.
    Zielpunkte UND Platzpunkte kommen aus demselben Strom (wie in den Vorgängerdemos); der Anfangsbesitz kommt aus
    einem eigenen, davon unabhängigen Strom (`OWNER_STREAM_XOR`)."""
    rng = SplitMix64(seed)
    lo, hi = 15, MAP_SIZE - 15
    centres = [(lo + rng.below(hi - lo + 1), lo + rng.below(hi - lo + 1)) for _ in range(N_CENTRES)]

    def point():
        ux, uy = rng.below(MAP_SIZE + 1), rng.below(MAP_SIZE + 1)
        cx, cy = centres[rng.below(N_CENTRES)]
        jx, jy = rng.below(21) - 10, rng.below(21) - 10
        x = ((100 - ballung) * ux + ballung * (cx + jx)) // 100
        y = ((100 - ballung) * uy + ballung * (cy + jy)) // 100
        return min(max(x, 0), MAP_SIZE), min(max(y, 0), MAP_SIZE)

    targets = [point() for _ in range(n)]
    slots = [point() for _ in range(n)]
    owner_rng = SplitMix64(seed ^ OWNER_STREAM_XOR)
    owner = _shuffle(n, owner_rng)
    return from_points(targets, slots, owner)


# --- feste Karten (Lehrbuchfälle), dieselbe Geometrie wie die Zufallskarten -----------------------------------------

def textbook_example():
    """Von Hand nachvollzogene Karte (n=5): Anfangsbesitz `[0,1,2,3,4]` (jeder besitzt anfangs "seinen eigenen" Platz
    im Index, aber die PRÄFERENZEN sind unabhängig davon gesetzt, siehe `lists` unten - der Anfangsbesitz an sich ist
    hier bewusst die Identität, weil die Listen selbst schon dafür sorgen, dass niemand seinen eigenen Platz zuerst
    will). Präferenzen `[[1,0,2,3,4],[2,1,0,3,4],[0,2,1,3,4],[0,4,3,1,2],[2,3,4,0,1]]`. Runde 1: ein 3-Kreis
    (0→1→2→0); Runde 2: ein 2-Kreis (3,4). Ergebnis `[1,2,0,4,3]` - jeder verbessert sich um genau 1 Rangplatz.
    Positionen sind reine Dekoration (nicht kostenwirksam, da `lists` gesetzt ist)."""
    targets = [(10 + 20 * i, 30) for i in range(5)]
    slots = [(10 + 20 * s, 70) for s in range(5)]
    owner = (0, 1, 2, 3, 4)
    lists = ((1, 0, 2, 3, 4), (2, 1, 0, 3, 4), (0, 2, 1, 3, 4), (0, 4, 3, 1, 2), (2, 3, 4, 0, 1))
    return from_points(targets, slots, owner, lists=lists)


def worst_case(n=20):
    """Θ(n²)-Worst-Case: alle Personen haben dieselbe Präferenzliste `0,1,2,...,n-1`, Anfangsbesitz = Identität.
    Jede Runde tauscht genau 2 Plätze (Person 0 bekommt Platz 0, ein Zweierkreis am Ende ODER eine Selbstschleife -
    tatsächlich läuft es auf genau eine Selbstschleife pro Runde hinaus, siehe `tt_ttc.py`-Tests): das ist die Karte,
    an der `Schritte / n²` gemessen wird. Positionen sind Dekoration (`lists` gesetzt)."""
    targets = [(10 + 5 * i, 30) for i in range(n)]
    slots = [(10 + 5 * s, 70) for s in range(n)]
    owner = tuple(range(n))
    lists = tuple(tuple(range(n)) for _ in range(n))
    return from_points(targets, slots, owner, lists=lists)


def dead_swap_example(n=20):
    """Negativkontrolle (bewusst gezeigt, nicht versteckt): Anfangsbesitz = Identität AUF DENSELBEN PUNKTEN wie die
    Zielpunkte (Platz s liegt exakt auf Zielpunkt s) - jeder besitzt bereits (fast) seinen besten Platz, fast niemand
    tauscht. Zeigt, warum die unabhängige Besitz-Permutation in `generate()` tragend ist: ohne sie wäre JEDE Karte so."""
    targets = [(10 + 4 * i, 50) for i in range(n)]
    slots = targets
    owner = tuple(range(n))
    return from_points(targets, slots, owner)


NETS = {
    "textbook": lambda n: textbook_example(),
    "worst_case": lambda n: worst_case(n),
    "dead_swap": lambda n: dead_swap_example(n),
}


def build(net, n, ballung, seed):
    """Karte zu den Einstellungen; feste Karten ignorieren die Zufallsparameter (Θ(n²)-Karte und Negativkontrolle
    nehmen `n` noch entgegen, weil ihre Größe variabel ist)."""
    if net in NETS:
        return NETS[net](n)
    return generate(n, ballung, seed)
