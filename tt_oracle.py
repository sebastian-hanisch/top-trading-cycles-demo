"""Orakel für Tests: Brute Force über ALLE Permutationen (= alle möglichen vollständigen Zuordnungen), unabhängig von
`tt_ttc.py` hergeleitet - exakt das Muster von `hr_oracle.py`/`sr_oracle.py`: erst JEDE vollständige Kandidatenlösung
erzeugen (hier: jede Permutation, kein Pruning nötig, da es keine Kapazitäts- oder Erreichbarkeits-Einschränkung
gibt), Stabilität/Effizienz erst als unabhängigen, zweiten Schritt prüfen - nie während der Konstruktion.

Geprüft wird KERN-Stabilität (keine Koalition kann durch internen Neu-Tausch alle Mitglieder mindestens gleich und
mindestens eines strikt besser stellen), individuelle Rationalität UND Pareto-Effizienz gleichzeitig: dieselbe
Koalitions-Blockade-Prüfung deckt alle drei ab (eine Koalition der Größe 1 = individuelle Rationalität, eine Koalition
aller n = ein Pareto-verbessernder Tausch für alle). Nur für kleine n gedacht (n <= ~9): die Prüfung selbst braucht
für jeden Kandidaten die Potenzmenge der Koalitionen (2^n) - bei n=9 sind das 511 nichtleere Koalitionen je einem der
9! = 362880 Kandidaten, in der Praxis noch schnell genug für Tests."""

import itertools

PRACTICAL_MAX_N = 9


def _ranks(prefs):
    return [{x: k for k, x in enumerate(p)} for p in prefs]


def blocking_coalition(prefs, owner, pairs):
    """Eine blockierende Koalition (Teilmenge von Personen, die durch internen Neu-Tausch NUR ihrer eigenen
    Ausgangsplätze alle mindestens so gut und mindestens eine strikt besser stellen kann) oder None. Geprüft wird
    jede nichtleere Teilmenge S: kann man die Plätze {owner[i]: i in S} so unter S neu verteilen (jede Permutation
    von S auf sich selbst), dass jedes Mitglied mindestens seinen jetzigen Rang behält und mindestens eines sich
    verbessert? Das ist die Standard-Kern-Definition für Wohnungsmärkte (Shapley & Scarf 1974; Roth & Postlewaite
    1977 zeigen, dass genau die TTC-Zuordnung diese Bedingung erfüllt und die einzige ist, die es tut)."""
    n = len(prefs)
    ranks = _ranks(prefs)
    mp = dict(pairs)
    people = list(range(n))
    for size in range(1, n + 1):
        for coalition in itertools.combinations(people, size):
            own_slots = [owner[i] for i in coalition]
            cur_ranks = [ranks[i][mp[i]] for i in coalition]
            for perm in itertools.permutations(own_slots):
                new_ranks = [ranks[coalition[k]][perm[k]] for k in range(size)]
                if all(nr <= cr for nr, cr in zip(new_ranks, cur_ranks)) and any(nr < cr for nr, cr in zip(new_ranks, cur_ranks)):
                    return coalition
    return None


def is_core_stable(prefs, owner, pairs):
    return blocking_coalition(prefs, owner, pairs) is None


def _complete_assignments(n):
    """Jede vollständige Zuordnung (= jede Permutation von Plätzen auf Personen) - kein Pruning nötig, da alle
    Plätze für alle Personen erreichbar sind (kein Kapazitäts- oder Reichweiten-Filter wie bei den anderen
    Matching-Stücken)."""
    for perm in itertools.permutations(range(n)):
        yield tuple(enumerate(perm))


def core_assignment_brute(prefs, owner):
    """Die (bei strikten Präferenzen eindeutige) kernstabile Zuordnung, oder None (sollte bei strikten Präferenzen
    nie vorkommen - der Kern eines Wohnungsmarkts ist nach Shapley & Scarf 1974 nie leer)."""
    n = len(prefs)
    for assignment in _complete_assignments(n):
        if is_core_stable(prefs, owner, assignment):
            return assignment
    return None


def all_core_assignments_brute(prefs, owner, max_n=PRACTICAL_MAX_N):
    """ALLE kernstabilen Zuordnungen (für die Eindeutigkeitsmessung - bei strikten Präferenzen ist der Kern nach
    Roth & Postlewaite 1977 eine einzige Zuordnung, hier unabhängig nachgeprüft statt angenommen)."""
    n = len(prefs)
    if n > max_n:
        raise ValueError(f"all_core_assignments_brute: n={n} > max_n={max_n}")
    found = []
    for assignment in _complete_assignments(n):
        if is_core_stable(prefs, owner, assignment):
            found.append(assignment)
    return found
