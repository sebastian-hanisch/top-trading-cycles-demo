"""Top Trading Cycles (Gale, in Shapley & Scarf 1974): jeder verbleibende Teilnehmer zeigt auf den aktuellen Besitzer
seines besten VERBLEIBENDEN Platzes (Selbstschleife erlaubt, falls der eigene Platz das ist); da jeder Knoten
Außengrad 1 hat, gibt es in jeder Runde mindestens einen Kreis. Jeder Teilnehmer in einem gefundenen Kreis bekommt den
Platz, auf den er zeigt, und verlässt mit ihm den Markt; wiederholen, bis niemand mehr übrig ist.

Kernvariable: `owner_of_slot[s]` (FEST, niemals aktualisiert) = die Person, die Platz s URSPRÜNGLICH besitzt. Ein
Platz ist verfügbar, solange seine ursprüngliche Besitzerin noch aktiv (im Markt) ist - ein Platz wird also NIE zum
"neuen Eigentum" des Empfängers umgeschrieben, nur der ursprüngliche Besitzer zählt für die Buchführung (der im
Prototyp explizit benannte Stolperstein: eine naive Implementierung, die `owner_of_slot` nach jedem Kreis auf den
Empfänger umschreibt, würde in der nächsten Runde falsche Ziele berechnen). `cursor[i]`: monoton wachsender Zeiger in
i's eigener, VOLLSTÄNDIGEN Präferenzliste - übersprungene (nicht mehr verfügbare) Einträge werden nie erneut geprüft.

Kreissuche je Runde: 3-Farben-Markierung (unbesucht/auf-dem-Pfad/fertig) über die noch aktiven Teilnehmer; ein Kreis
ist gefunden, sobald die Verfolgung einen noch "auf-dem-Pfad"-Knoten erneut trifft. Kein Union-Find nötig (Außengrad
immer exakt 1). Mehrere disjunkte Kreise können in derselben Runde gefunden werden (ihre Ziele hängen nur von den zu
Rundenbeginn berechneten Zeigern ab) - das ist Standard-TTC (Bulk-Entfernung je Runde), keine eigene Optimierung.

Aufwand = Listenvorrücken (Zeiger-Schritte, die einen nicht mehr verfügbaren Platz überspringen) + Verfolgungsschritte
(Kanten, die die Kreissuche entlangläuft), NIE Sekunden. Ereignisprotokoll für die Wiedergabe (`state_at`-Muster wie
in allen Vorgängerdemos): "advance" (Zeiger übersprang einen nicht mehr verfügbaren Platz), "point" (Person zeigt auf
ihren aktuellen Favoriten), "cycle" (ein Kreis wurde gefunden und sofort aufgelöst).

Der Kreissucher bleibt bewusst generisch (keine Kompatibilitätsmaske, kein Längenlimit eingebaut) - die
Kreislängen-Analyse lebt ausschließlich in `tt_evaluation.py` als Statistik ÜBER das unveränderte TTC-Ergebnis, nicht
im Algorithmus selbst, damit eine spätere Nierentausch-Demo hier andocken kann, ohne diesen Kern anzufassen."""

from dataclasses import dataclass

EV_ADVANCE = "advance"
EV_POINT = "point"
EV_CYCLE = "cycle"


@dataclass(frozen=True)
class Event:
    kind: str
    round: int
    person: int = -1
    slot: int = -1           # advance: übersprungener Platz; point: Zielplatz
    owner: int = -1           # point: ursprünglicher Besitzer des Zielplatzes (= die Person, auf die i zeigt)
    cycle: tuple = None        # cycle: Personen in Kreisreihenfolge
    received: tuple = None      # cycle: je Person aus `cycle`, welchen Platz sie bekommt (gleiche Reihenfolge)


@dataclass(frozen=True)
class Result:
    pairs: tuple           # ((Person, Platz), ...) nach Person sortiert
    events: tuple            # Event-Protokoll, siehe oben
    advances: int              # Anzahl Listenvorrücken
    trace_steps: int             # Anzahl Verfolgungsschritte (Kanten der Kreissuche)
    rounds: int                    # Anzahl Runden
    cycle_lengths: tuple              # Länge jedes gefundenen Kreises, in Findereihenfolge

    @property
    def steps(self):
        return self.advances + self.trace_steps

    @property
    def n_events(self):
        return len(self.events)

    @property
    def n_cycles(self):
        return len(self.cycle_lengths)


def solve(prefs, owner, record=True):
    """`prefs[i]` = VOLLSTÄNDIGE, strikte Präferenzliste von Person i über alle n Plätze (bester zuerst). `owner[i]`
    = Platz, den i zu Beginn besitzt (Permutation von 0..n-1). Terminiert immer: in jeder Runde verlässt mindestens
    eine Person den Markt (die kürzeste mögliche Selbstschleife ist immer ein gültiger Kreis)."""
    n = len(prefs)
    owner_of_slot = [0] * n
    for i, s in enumerate(owner):
        owner_of_slot[s] = i
    active = [True] * n
    cursor = [0] * n
    result = [None] * n
    events = []
    advances = trace_steps = rounds = 0
    cycle_lengths = []
    remaining = set(range(n))

    while remaining:
        rounds += 1
        target = {}
        for i in remaining:
            while not active[owner_of_slot[prefs[i][cursor[i]]]]:
                if record:
                    events.append(Event(EV_ADVANCE, rounds, person=i, slot=prefs[i][cursor[i]]))
                cursor[i] += 1
                advances += 1
            s = prefs[i][cursor[i]]
            ow = owner_of_slot[s]
            target[i] = ow
            if record:
                events.append(Event(EV_POINT, rounds, person=i, slot=s, owner=ow))

        color = {i: 0 for i in remaining}   # 0 unbesucht, 1 auf dem Pfad, 2 fertig (in einem Kreis ODER führt in einen)
        for start in list(remaining):
            if color[start] != 0:
                continue
            path = []
            i = start
            while color[i] == 0:
                color[i] = 1
                path.append(i)
                i = target[i]
                trace_steps += 1
            if color[i] == 1:
                idx = path.index(i)
                cyc = tuple(path[idx:])
                for p in cyc:
                    color[p] = 2
                received = tuple(prefs[p][cursor[p]] for p in cyc)
                for p, s in zip(cyc, received):
                    result[p] = s
                    active[p] = False
                remaining -= set(cyc)
                cycle_lengths.append(len(cyc))
                if record:
                    events.append(Event(EV_CYCLE, rounds, cycle=cyc, received=received))
                for p in path[:idx]:
                    color[p] = 2
            else:
                for p in path:
                    color[p] = 2

    pairs = tuple(sorted((i, result[i]) for i in range(n)))
    return Result(pairs, tuple(events), advances, trace_steps, rounds, tuple(cycle_lengths))


def state_at(res, n, k):
    """Zustand nach den ersten k Ereignissen: wer hat schon (mit welchem Platz) den Markt verlassen, aktueller
    Zeigerstand je Person, und der zuletzt gefundene Kreis (für die Kartenfärbung)."""
    matched, cursor_advance = {}, [0] * n
    last_cycle, last_received = None, None
    for e in res.events[:k]:
        if e.kind == EV_ADVANCE:
            cursor_advance[e.person] += 1
        elif e.kind == EV_CYCLE:
            for p, s in zip(e.cycle, e.received):
                matched[p] = s
            last_cycle, last_received = e.cycle, e.received
    left = set(matched)
    return {"matched": matched, "left": left, "cursor_advance": cursor_advance, "last_cycle": last_cycle, "last_received": last_received}


def is_valid(pairs, n):
    people = [i for i, _ in pairs]
    slots = [s for _, s in pairs]
    return sorted(people) == list(range(n)) and sorted(slots) == list(range(n))


def individually_rational(prefs, owner, pairs):
    """Niemand ist schlechter dran als mit dem eigenen Ausgangsplatz (notwendig für Core-Stabilität)."""
    ranks = [{x: k for k, x in enumerate(p)} for p in prefs]
    return all(ranks[i][s] <= ranks[i][owner[i]] for i, s in pairs)


def pair_swap_blocks(prefs, pairs):
    """Gibt es zwei Personen, die durch Tausch ihrer ERHALTENEN Plätze beide strikt gewinnen würden? Billige,
    notwendige (nicht hinreichende) Zusatzprüfung, immer in der App gezeigt - volle Core-Stabilität über ALLE
    Koalitionsgrößen prüft nur `tt_oracle.py` (nur für kleine n, in den Tests)."""
    ranks = [{x: k for k, x in enumerate(p)} for p in prefs]
    mp = dict(pairs)
    out = []
    people = sorted(mp)
    for a_idx, i in enumerate(people):
        for j in people[a_idx + 1:]:
            if ranks[i][mp[j]] < ranks[i][mp[i]] and ranks[j][mp[i]] < ranks[j][mp[j]]:
                out.append((i, j))
    return out


def certificate(prefs, owner, res):
    """S1 gültige Permutation, S2 individuelle Rationalität, S3 kein blockierendes Zweiertausch-Paar. Notwendige
    (nicht hinreichende) In-App-Prüfungen; die erschöpfende Core-Stabilitätsprüfung lebt in `tt_oracle.py`."""
    n = len(prefs)
    swaps = pair_swap_blocks(prefs, res.pairs)
    cert = {"s1_valid": is_valid(res.pairs, n), "s2_individually_rational": individually_rational(prefs, owner, res.pairs),
            "s3_no_pair_swap": not swaps, "pair_swaps": swaps}
    cert["all_ok"] = cert["s1_valid"] and cert["s2_individually_rational"] and cert["s3_no_pair_swap"]
    return cert
