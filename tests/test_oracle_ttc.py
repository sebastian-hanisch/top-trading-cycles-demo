"""Unabhängige Orakel zu Top Trading Cycles.

1. Ein eigener TTC, der in jedem Schritt genau EINEN Kreis entfernt (statt je Runde alle, ohne Zeiger/Farbmarkierung): gleiche Zuordnung,
   Kreislängen = Zyklentyp der Tauschpermutation, Rundenzahl.
2. Kern-Eindeutigkeit (Roth & Postlewaite 1977) mit einem anderen Blockadetest als `tt_oracle.py`: eine Koalition blockiert genau dann, wenn
   das Zuweisungsproblem 'jeder bekommt einen Ausgangsplatz der Koalition, nie schlechter, mindestens einmal besser' lösbar ist
   (`scipy.optimize.linear_sum_assignment` statt Permutationsaufzählung).
3. Worst-Case-Kennzahl: Schritte / n^2 = 1 (n^2 Schritte genau)."""

import itertools
import random

import pytest

import tt_scenario as S
from tt_preferences import preferences
from tt_ttc import solve

lsa = pytest.importorskip("scipy.optimize").linear_sum_assignment


def _my_ttc(prefs, owner):
    n = len(prefs)
    house_owner = {owner[i]: i for i in range(n)}
    rem, alloc, cycles = set(range(n)), {}, []
    while rem:
        i, seen = min(rem), []
        while i not in seen:
            seen.append(i)
            i = house_owner[next(h for h in prefs[i] if house_owner[h] in rem)]
        cyc = seen[seen.index(i):]
        for p in cyc:
            alloc[p] = next(h for h in prefs[p] if house_owner[h] in rem)
        cycles.append(len(cyc))
        rem -= set(cyc)
    return alloc, sorted(cycles)


def _blocks(prefs, owner, alloc, coalition):
    k = len(coalition)
    rk = [{h: r for r, h in enumerate(p)} for p in prefs]
    w = [[-10 ** 6] * k for _ in range(k)]
    for a, i in enumerate(coalition):
        for b, j in enumerate(coalition):
            r_new, r_cur = rk[i][owner[j]], rk[i][alloc[i]]
            if r_new <= r_cur:
                w[a][b] = 1 if r_new < r_cur else 0
    rows, cols = lsa([[-x for x in row] for row in w])
    return sum(w[r][c] for r, c in zip(rows, cols)) >= 1


def _is_core(prefs, owner, alloc):
    n = len(prefs)
    return not any(_blocks(prefs, owner, alloc, s) for size in range(1, n + 1) for s in itertools.combinations(range(n), size))


def test_ttc_equals_one_cycle_at_a_time_reimplementation():
    rng = random.Random(77)
    for _ in range(250):
        n = rng.randint(1, 30)
        owner = list(range(n))
        rng.shuffle(owner)
        if rng.random() < 0.3:
            base = rng.sample(range(n), n)
            prefs = [list(base) for _ in range(n)]
        else:
            prefs = [rng.sample(range(n), n) for _ in range(n)]
        res = solve(prefs, owner, record=rng.random() < 0.5)
        alloc, cycles = _my_ttc(prefs, owner)
        assert dict(res.pairs) == alloc
        assert sorted(res.cycle_lengths) == cycles


def test_ttc_is_the_unique_core_allocation_on_small_markets():
    rng = random.Random(3)
    for _ in range(40):
        n = rng.randint(2, 4)
        owner = list(range(n))
        rng.shuffle(owner)
        prefs = [rng.sample(range(n), n) for _ in range(n)]
        ttc = dict(solve(prefs, owner, record=False).pairs)
        for perm in itertools.permutations(range(n)):
            alloc = dict(enumerate(perm))
            assert _is_core(prefs, owner, alloc) == (alloc == ttc)


def test_blocking_detector_sanity():
    assert not _is_core([[1, 0], [0, 1]], [0, 1], {0: 0, 1: 1})
    assert _is_core([[1, 0], [0, 1]], [0, 1], {0: 1, 1: 0})


def test_worst_case_steps_are_exactly_n_squared():
    for n in (10, 40):
        sc = S.worst_case(n)
        assert solve(preferences(sc, "dist"), sc.owner, record=False).steps == n * n
