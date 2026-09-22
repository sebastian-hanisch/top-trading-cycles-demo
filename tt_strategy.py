"""Manipulation: lohnt es sich, eine falsche Präferenzliste anzugeben? Erschöpfend über ALLE Permutationen der
eigenen Liste (nur kleine Karten - TTC-Listen sind immer vollständig, es gibt kein sinnvolles Kürzen wie bei
Gale-Shapleys reichweitenbedingt unvollständigen Listen).

Roth (1982, "Incentive compatibility in a market with indivisible goods", Economics Letters) zeigt: der Kern-
Mechanismus (= TTC, siehe `tt_oracle.py`s Core-Definition) ist strategiefest - kein Teilnehmer kann sich durch eine
falsche Angabe verbessern. Gemessen wird das hier, nicht angenommen."""

import itertools

from tt_ttc import solve


def _rank_of(prefs, owner, i, reported):
    """Bei den gemeldeten Präferenzen `reported` (nur Person i's Liste ersetzt), welchen PLATZ bekommt i, und wie
    ist dessen Rang in i's WAHRER Liste?"""
    res = solve(reported, owner, record=False)
    mp = dict(res.pairs)
    true_rank = {x: k for k, x in enumerate(prefs[i])}
    return true_rank[mp[i]]


def best_response(prefs, owner, i):
    """(Rang ehrlich, bester erreichbarer Rang, beste gefundene Meldung) für Person i, exhaustiv über alle
    Permutationen ihrer eigenen Liste (die Listen der anderen bleiben ehrlich)."""
    n = len(prefs)
    honest = _rank_of(prefs, owner, i, prefs)
    best, best_report = honest, list(prefs[i])
    for perm in itertools.permutations(range(n)):
        if list(perm) == list(prefs[i]):
            continue
        reported = [list(p) for p in prefs]
        reported[i] = list(perm)
        r = _rank_of(prefs, owner, i, reported)
        if r < best:
            best, best_report = r, list(perm)
    return honest, best, best_report
