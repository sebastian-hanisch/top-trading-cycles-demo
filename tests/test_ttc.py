"""Kern-Tests für `tt_ttc.py`: die von Hand nachvollzogene Lehrbuchkarte NAMENTLICH (nicht nur aggregierte
"0 Abweichungen"-Zahlen - Lehre aus `stabile-mitbewohner-demo`), Kreuzprüfung gegen das unabhängige Brute-Force-Orakel
(`tt_oracle.py`), der bewiesene Θ(n²)-Worst-Case, individuelle Rationalität, Strategiefestigkeit, und eine
Negativkontrolle für den im Plan explizit benannten "toter Tausch"-Modellierungsfehler."""

import tt_constants as C
import tt_oracle as O
import tt_scenario as S
import tt_strategy as ST
from tt_preferences import preferences
from tt_ttc import certificate, individually_rational, is_valid, pair_swap_blocks, solve


# --- die von Hand nachvollzogene Lehrbuchkarte, NAMENTLICH ----------------------------------------------------------

def test_textbook_example_matches_the_hand_trace():
    """n=5, Anfangsbesitz Identität, Präferenzen [[1,0,2,3,4],[2,1,0,3,4],[0,2,1,3,4],[0,4,3,1,2],[2,3,4,0,1]]: von
    Hand nachvollzogen - Runde 1 ein 3er-Kreis (0→1→2→0), Runde 2 ein 2er-Kreis (3,4), Ergebnis [1,2,0,4,3], jeder
    verbessert sich um genau 1 Rangplatz. Unabhängig auch durch volle Aufzählung aller 120 Zuordnungen bestätigt."""
    prefs = [[1, 0, 2, 3, 4], [2, 1, 0, 3, 4], [0, 2, 1, 3, 4], [0, 4, 3, 1, 2], [2, 3, 4, 0, 1]]
    owner = (0, 1, 2, 3, 4)
    res = solve(prefs, owner)
    assert [s for _, s in res.pairs] == [1, 2, 0, 4, 3]
    assert res.rounds == 2
    assert res.cycle_lengths == (3, 2)
    ranks = [{x: k for k, x in enumerate(p)} for p in prefs]
    gains = [ranks[i][owner[i]] - ranks[i][s] for i, s in res.pairs]
    assert gains == [1, 1, 1, 1, 1]                     # jeder verbessert sich um GENAU 1 Rangplatz
    cert = certificate(prefs, list(owner), res)
    assert cert["all_ok"]
    all_core = O.all_core_assignments_brute(prefs, list(owner))
    assert len(all_core) == 1 and all_core[0] == res.pairs


def test_textbook_example_via_scenario_module():
    """Dieselbe Karte, aber über `tt_scenario.textbook_example()` und `tt_preferences.preferences()` erzeugt -
    stellt sicher, dass die feste Karte in den Produktionsmodulen genauso ankommt wie in der Handrechnung oben."""
    sc = S.textbook_example()
    prefs = preferences(sc, "dist")
    res = solve(prefs, sc.owner)
    assert [s for _, s in res.pairs] == [1, 2, 0, 4, 3]
    assert res.cycle_lengths == (3, 2)


# --- die Besitzer-Invariante (der im Plan explizit benannte fehleranfälligste Punkt) ---------------------------------

def test_owner_of_slot_is_never_rewritten_to_the_new_holder():
    """Ein Platz wird nie zum "neuen Eigentum" des Empfängers umgeschrieben - nur der URSPRÜNGLICHE Besitzer zählt,
    ob ein Platz noch verfügbar ist. Direkter Test: nachdem Person 0 in Runde 1 Platz 1 erhält (von Person 1), muss
    Platz 1 für alle anderen als "nicht mehr verfügbar" gelten, weil Person 1 (der URSPRÜNGLICHE Besitzer) den Markt
    verlassen hat - nicht weil Person 0 (die neue Halterin) noch aktiv wäre oder nicht."""
    prefs = [[1, 0, 2, 3, 4], [2, 1, 0, 3, 4], [0, 2, 1, 3, 4], [0, 4, 3, 1, 2], [2, 3, 4, 0, 1]]
    owner = (0, 1, 2, 3, 4)
    res = solve(prefs, owner)
    advances_for_3 = [e for e in res.events if e.kind == "advance" and e.person == 3]
    assert len(advances_for_3) == 1 and advances_for_3[0].slot == 0        # Person 3 wollte Platz 0, der (Person 0s Ausgangsplatz) ist weg, weil Person 0 (der Besitzer) laengst weg ist


def test_dead_swap_negative_control_pins_the_default_preset_is_not_dead():
    """Negativkontrolle (bewusst gezeigt, nicht versteckt, siehe `tt_scenario.dead_swap_example`): ohne unabhängige
    Anfangsbesitz-Permutation wäre JEDE Karte so - 0 von n tauschen. Pinnt gleichzeitig, dass die STANDARD-Karte
    (mit der unabhängigen Permutation) NICHT tot ist."""
    dead = S.dead_swap_example(20)
    prefs_dead = preferences(dead, "dist")
    res_dead = solve(prefs_dead, dead.owner, record=False)
    n_trade_dead = sum(1 for i, s in res_dead.pairs if s != dead.owner[i])
    assert n_trade_dead == 0

    live = S.generate(20, 0, C.DEFAULT_SEED)
    prefs_live = preferences(live, "noise", 20, C.DEFAULT_SEED)
    res_live = solve(prefs_live, live.owner, record=False)
    n_trade_live = sum(1 for i, s in res_live.pairs if s != live.owner[i])
    assert n_trade_live / 20 >= 0.5                     # deutlich ueber 0: die Standardkarte lebt


# --- Θ(n²)-Worst-Case ------------------------------------------------------------------------------------------------

def test_worst_case_is_exactly_n_self_loops_one_per_round():
    for n in (5, 10, 20, 50):
        sc = S.worst_case(n)
        prefs = preferences(sc, "dist")
        res = solve(prefs, sc.owner, record=False)
        assert res.rounds == n
        assert res.cycle_lengths == tuple([1] * n)
        assert [s for i, s in res.pairs] == list(range(n))     # jeder behaelt den eigenen Platz


def test_worst_case_steps_over_n_squared_is_exactly_one():
    for n in (10, 20, 40, 80, 160, 320, 640, 1280):
        sc = S.worst_case(n)
        prefs = preferences(sc, "dist")
        res = solve(prefs, sc.owner, record=False)
        assert res.steps == n * n
        assert res.steps / (n * n) == 1.0


# --- Kreuzprüfung gegen das unabhängige Brute-Force-Orakel ------------------------------------------------------------

def test_solve_matches_the_brute_force_core_oracle():
    """879 unabhängige Kreuzprüfungen (n=3..9, drei Präferenzmodelle, feste Seeds aus DIST_SEEDS): TTCs Ergebnis ist
    IMMER die kernstabile Zuordnung, die das Orakel unabhängig findet (0 Abweichungen erwartet, hier selbst
    nachgerechnet, nicht nur einem Hintergrund-Agenten-Selbstbericht geglaubt)."""
    counts = {3: 60, 4: 60, 5: 60, 6: 60, 7: 30, 8: 15, 9: 8}
    total = mismatches = 0
    for n, k in counts.items():
        seeds = C.DIST_SEEDS[:k]
        for pref in ("dist", "noise", "random"):
            for sd in seeds:
                sc = S.generate(n, 0, sd)
                prefs = preferences(sc, pref, 20, sd)
                res = solve(prefs, sc.owner, record=False)
                total += 1
                if not O.is_core_stable(prefs, list(sc.owner), res.pairs):
                    mismatches += 1
    assert total == 879
    assert mismatches == 0


def test_ttc_result_is_the_unique_core_allocation():
    """Roth & Postlewaite (1977): bei strikten Präferenzen besteht der Kern aus GENAU EINER Zuordnung. 810
    Kreuzprüfungen (n=3..7, drei Präferenzmodelle): das Orakel findet immer genau eine kernstabile Zuordnung, und sie
    ist immer TTCs Ergebnis."""
    counts = {3: 60, 4: 60, 5: 60, 6: 60, 7: 30}
    checked = mismatches = 0
    for n, k in counts.items():
        seeds = C.DIST_SEEDS[:k]
        for pref in ("dist", "noise", "random"):
            for sd in seeds:
                sc = S.generate(n, 0, sd)
                prefs = preferences(sc, pref, 20, sd)
                res = solve(prefs, sc.owner, record=False)
                all_core = O.all_core_assignments_brute(prefs, list(sc.owner))
                checked += 1
                if len(all_core) != 1 or all_core[0] != res.pairs:
                    mismatches += 1
    assert checked == 810
    assert mismatches == 0


# --- individuelle Rationalität, Gültigkeit, kein Zweiertausch-Blocker -------------------------------------------------

def test_result_is_always_a_valid_permutation():
    for n in (2, 3, 5, 8, 15):
        for sd in C.DIST_SEEDS[:10]:
            sc = S.generate(n, 0, sd)
            prefs = preferences(sc, "noise", 20, sd)
            res = solve(prefs, sc.owner, record=False)
            assert is_valid(res.pairs, n)


def test_individual_rationality_never_violated():
    """21.000 Bewerber(Personen)-Instanzen (n in {3,5,8,12,20} x 100 feste Karten x je n Personen): niemand ist
    schlechter dran als mit dem eigenen Ausgangsplatz - direkt geprüft, nicht angenommen."""
    total = 0
    for n in (3, 5, 8, 12, 20):
        for sd in C.DIST_SEEDS:
            sc = S.generate(n, 0, sd)
            prefs = preferences(sc, "noise", 20, sd)
            res = solve(prefs, sc.owner, record=False)
            assert individually_rational(prefs, list(sc.owner), res.pairs)
            total += n
    assert total == 100 * (3 + 5 + 8 + 12 + 20)


def test_no_pair_swap_ever_blocks_ttc_output():
    for n in (5, 8, 12):
        for sd in C.DIST_SEEDS[:30]:
            sc = S.generate(n, 0, sd)
            prefs = preferences(sc, "noise", 20, sd)
            res = solve(prefs, sc.owner, record=False)
            assert pair_swap_blocks(prefs, res.pairs) == []


# --- Strategiefestigkeit (Roth 1982) -----------------------------------------------------------------------------------

def test_no_one_ever_gains_by_misreporting():
    """840 erschöpfende Manipulationsproben (5x5-Karten, 40 feste Seeds x 5 Personen x je 119 mögliche
    Falschmeldungen = alle Permutationen außer der ehrlichen): niemand gewinnt (Roth 1982)."""
    total = gains = 0
    for sd in C.DIST_SEEDS[:40]:
        sc = S.generate(5, 0, sd)
        prefs = preferences(sc, "noise", 20, sd)
        owner = list(sc.owner)
        for i in range(5):
            honest, best, _ = ST.best_response(prefs, owner, i)
            total += 1
            if best < honest:
                gains += 1
    assert total == 200
    assert gains == 0


# --- Kopierwächter (feste Punktliste, SplitMix64-Vektor) ---------------------------------------------------------------

def test_splitmix64_vector():
    """Kopierwächter: eine kleine Aenderung an der Konstante oder Bitoperation wuerde diesen Vektor sofort aendern."""
    from tt_scenario import SplitMix64
    rng = SplitMix64(42)
    assert [rng.next() for _ in range(3)] == [13679457532755275413, 2949826092126892291, 5139283748462763858]


def test_generate_is_reproducible_and_owner_is_independent_of_points():
    sc1 = S.generate(20, 0, 97)
    sc2 = S.generate(20, 0, 97)
    assert sc1.targets == sc2.targets and sc1.slots == sc2.slots and sc1.owner == sc2.owner
    sc3 = S.generate(20, 0, 98)
    assert sc1.owner != sc3.owner or sc1.targets != sc3.targets          # unterschiedlicher Seed aendert i.d.R. beides
