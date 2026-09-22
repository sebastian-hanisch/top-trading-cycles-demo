"""Auswertung: eine Karte (`analyse`, `verdict`), viele Karten (`distribution`), Kreislängen-Histogramm,
Längenbeschränkungs-Vorschau (strukturelle Überleitung zu Nierentausch, KEINE neu berechnete Mechanik), Aufwand gegen
Größe, Manipulationsprobe. Alles ganzzahlig und deterministisch; nur die Anzeige-Statistiken (Anteile, Mittel,
Mediane) sind Gleitkomma. Mittel und Median stehen immer zusammen."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import tt_constants as C
from tt_preferences import DEFAULT_NOISE, preferences, ranks
from tt_scenario import build, generate
from tt_strategy import best_response
from tt_ttc import certificate, solve


@dataclass
class Analysis:
    scenario: object
    pref: str
    noise: int
    seed: int
    prefs: list
    result: object
    cert: dict


def analyse(sc, pref=C.DEFAULT_PREF, noise=DEFAULT_NOISE, seed=0):
    prefs = preferences(sc, pref, noise, seed)
    res = solve(prefs, sc.owner)
    cert = certificate(prefs, list(sc.owner), res)
    return Analysis(sc, pref, noise, seed, prefs, res, cert)


def _rank_of(prefs, i, s):
    return {x: k for k, x in enumerate(prefs[i])}[s]


def _mean_median(values):
    if not values:
        return {"mean": None, "median": None}
    return {"mean": float(np.mean(values)), "median": float(np.median(values))}


def verdict(a):
    sc, res, prefs = a.scenario, a.result, a.prefs
    n = sc.n
    own_rank = [_rank_of(prefs, i, sc.owner[i]) for i in range(n)]
    got_rank = [_rank_of(prefs, i, s) for i, s in res.pairs]
    traders = [i for i in range(n) if dict(res.pairs)[i] != sc.owner[i]]
    rank_gain = [own_rank[i] - got_rank[i] for i in range(n)]
    dist_gain = [int(sc.cost[i, sc.owner[i]]) - int(sc.cost[i, dict(res.pairs)[i]]) for i in range(n)]
    data = {"n": n, "n_traders": len(traders), "trade_share": len(traders) / n, "steps": res.steps, "advances": res.advances,
            "trace_steps": res.trace_steps, "rounds": res.rounds, "n_cycles": res.n_cycles, "cycle_lengths": res.cycle_lengths,
            "rank_gain_all": _mean_median(rank_gain), "rank_gain_traders": _mean_median([rank_gain[i] for i in traders]),
            "dist_gain_all": _mean_median(dist_gain), "dist_gain_traders": _mean_median([dist_gain[i] for i in traders]),
            "cert": a.cert}
    return data


def scenario_from_settings(card, n, ballung, seed):
    return build(card, n, ballung, seed)


# --- viele Karten ----------------------------------------------------------------------------------------------------

@lru_cache(maxsize=256)
def cell_rows(n, ballung, pref, noise, seeds):
    rows = []
    for sd in seeds:
        sc = generate(n, ballung, sd)
        prefs = preferences(sc, pref, noise, sd)
        res = solve(prefs, sc.owner, record=False)
        own_rank = [_rank_of(prefs, i, sc.owner[i]) for i in range(n)]
        mp = dict(res.pairs)
        got_rank = [_rank_of(prefs, i, mp[i]) for i in range(n)]
        traders = [i for i in range(n) if mp[i] != sc.owner[i]]
        rank_gain = [own_rank[i] - got_rank[i] for i in range(n)]
        dist_gain = [int(sc.cost[i, sc.owner[i]]) - int(sc.cost[i, mp[i]]) for i in range(n)]
        rows.append({"n_traders": len(traders), "steps": res.steps, "rounds": res.rounds, "cycle_lengths": res.cycle_lengths,
                     "rank_gain": rank_gain, "dist_gain": dist_gain, "traders": traders})
    return tuple(rows)


def _med(values):
    return float(np.median(values)) if len(values) else None


def distribution(n, ballung, pref=C.DEFAULT_PREF, noise=DEFAULT_NOISE, seeds=C.DIST_SEEDS):
    rows = cell_rows(n, ballung, pref, noise, tuple(seeds))
    trade_shares = [r["n_traders"] / n for r in rows]
    all_rank_gain = [g for r in rows for g in r["rank_gain"]]
    trader_rank_gain = [r["rank_gain"][i] for r in rows for i in r["traders"]]
    all_dist_gain = [g for r in rows for g in r["dist_gain"]]
    trader_dist_gain = [r["dist_gain"][i] for r in rows for i in r["traders"]]
    n_cycles = [len(r["cycle_lengths"]) for r in rows]
    steps = [r["steps"] for r in rows]
    all_lengths = [c for r in rows for c in r["cycle_lengths"]]
    length_hist = {L: sum(1 for c in all_lengths if c == L) for L in range(1, max(all_lengths, default=0) + 1)}
    return {"n_seeds": len(seeds), "trade_share_mean": float(np.mean(trade_shares)), "trade_share_median": _med(trade_shares),
            "rank_gain_all": _mean_median(all_rank_gain), "rank_gain_traders": _mean_median(trader_rank_gain),
            "dist_gain_all": _mean_median(all_dist_gain), "dist_gain_traders": _mean_median(trader_dist_gain),
            "n_cycles": _mean_median(n_cycles), "steps": _mean_median(steps), "n_cycles_total": len(all_lengths),
            "length_hist": length_hist, "length_hist_share": {L: c / max(len(all_lengths), 1) for L, c in length_hist.items()}}


@lru_cache(maxsize=64)
def length_cap_preview(n, ballung, pref=C.DEFAULT_PREF, noise=DEFAULT_NOISE, seeds=C.DIST_SEEDS, caps=C.LENGTH_CAPS):
    """STRUKTURELLE Vorschau (keine neue Mechanik!): wie viel vom TTC-eigenen, unbeschränkten Gewinn ginge verloren,
    würde man Kreise nachträglich auf eine Höchstlänge filtern (nur Kreise <= cap zählen, längere werden verworfen,
    ihre Mitglieder behalten ihren Ausgangsplatz)? Motiviert Nierentausch (kurze Zyklen wegen Simultan-OPs), ist aber
    KEINE Nierentausch-Zahl - nur TTCs eigenes Ergebnis nachträglich gefiltert."""
    totals_rank = totals_dist = 0.0
    kept_rank = {c: 0.0 for c in caps}
    kept_dist = {c: 0.0 for c in caps}
    for sd in seeds:
        sc = generate(n, ballung, sd)
        prefs = preferences(sc, pref, noise, sd)
        res = solve(prefs, sc.owner, record=True)
        mp = dict(res.pairs)
        own_rank = [_rank_of(prefs, i, sc.owner[i]) for i in range(n)]
        got_rank = [_rank_of(prefs, i, mp[i]) for i in range(n)]
        rank_gain = [own_rank[i] - got_rank[i] for i in range(n)]
        dist_gain = [int(sc.cost[i, sc.owner[i]]) - int(sc.cost[i, mp[i]]) for i in range(n)]
        totals_rank += sum(rank_gain)
        totals_dist += sum(dist_gain)
        person_cycle_len = {}
        for e in res.events:
            if e.kind == "cycle":
                for p in e.cycle:
                    person_cycle_len[p] = len(e.cycle)
        for cap in caps:
            for i in range(n):
                if person_cycle_len.get(i, 1) <= cap:
                    kept_rank[cap] += rank_gain[i]
                    kept_dist[cap] += dist_gain[i]
    out = []
    for cap in caps:
        lost_rank = 1.0 - (kept_rank[cap] / totals_rank if totals_rank else 1.0)
        lost_dist = 1.0 - (kept_dist[cap] / totals_dist if totals_dist else 1.0)
        out.append({"cap": cap, "lost_rank_share": lost_rank, "lost_dist_share": lost_dist})
    return tuple(out)


@lru_cache(maxsize=8)
def effort_scaling(pref, noise, ns=C.EFFORT_NS, seeds=C.EFFORT_SEEDS):
    """Aufwand (Listenvorrücken + Verfolgungsschritte) gegen die Kartengröße auf der echten geometrischen Karte."""
    out = []
    for n in ns:
        steps = []
        for sd in seeds:
            sc = generate(n, 0, sd)
            prefs = preferences(sc, pref, noise, sd)
            steps.append(solve(prefs, sc.owner, record=False).steps)
        out.append({"n": n, "steps": float(np.mean(steps))})
    return tuple(out)


@lru_cache(maxsize=8)
def worst_case_scaling(ns=(10, 20, 40, 80, 160, 320, 640, 1280)):
    """Θ(n²)-Beleg: `Schritte / n²` an der Worst-Case-Karte (identische Präferenzliste, Identitätsbesitz)."""
    from tt_scenario import worst_case
    out = []
    for n in ns:
        sc = worst_case(n)
        prefs = preferences(sc, "dist")   # bei fester Liste (sc.lists gesetzt) irrelevant, welches Modell
        res = solve(prefs, sc.owner, record=False)
        out.append({"n": n, "steps": res.steps, "ratio": res.steps / (n * n)})
    return tuple(out)


@lru_cache(maxsize=8)
def manipulation(pref, noise, size=C.MANIP_SIZE, seeds=C.MANIP_SEEDS):
    """Erschöpfende Manipulationsprobe auf size x size-Karten: wer kann sich durch falsche Vorlieben verbessern?
    (Roth 1982: niemand - der Kern-Mechanismus ist strategiefest.)"""
    gain = total = 0
    for sd in seeds:
        sc = generate(size, 0, sd)
        prefs = preferences(sc, pref, noise, sd)
        owner = list(sc.owner)
        for i in range(size):
            honest, best, _ = best_response(prefs, owner, i)
            total += 1
            gain += best < honest
    return {"gain": gain, "total": total}


@lru_cache(maxsize=8)
def ir_check(pref, noise, ns=(3, 5, 8, 12, 20), seeds=C.DIST_SEEDS):
    """Individuelle Rationalität über viele Karten und Größen direkt geprüft (0 Verletzungen erwartet - Theorem)."""
    violations = total = 0
    for n in ns:
        for sd in seeds:
            sc = generate(n, 0, sd)
            prefs = preferences(sc, pref, noise, sd)
            res = solve(prefs, sc.owner, record=False)
            mp = dict(res.pairs)
            own_rank = [_rank_of(prefs, i, sc.owner[i]) for i in range(n)]
            got_rank = [_rank_of(prefs, i, mp[i]) for i in range(n)]
            for i in range(n):
                total += 1
                if got_rank[i] > own_rank[i]:
                    violations += 1
    return {"violations": violations, "total": total}
