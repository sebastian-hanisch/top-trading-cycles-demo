# Top Trading Cycles – Tausch ohne Geld – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-top-trading-cycles-demo.streamlit.app/)**

Zwölftes Stück der **Matching-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", dritte von vier Erweiterungen des Gale-Shapley-Asts (nach [stabile-mitbewohner-demo](https://github.com/sebastian-hanisch/stabile-mitbewohner-demo) und [krankenhaus-zulassung-demo](https://github.com/sebastian-hanisch/krankenhaus-zulassung-demo)) – inspiriert von Alvin Roths Arbeiten zu Marktdesign ohne Geld.

**Gale-Shapley und Krankenhaus-Zulassung** paaren Bewerber mit Anbietern (zwei Seiten). Hier besitzt **jeder schon etwas** und tauscht direkt: strukturell ein echter Bruch, kein Deferred-Acceptance-Verwandter. Gales Algorithmus (in Shapley & Scarf 1974, "The Core of an N Person Game") löst den **Wohnungsmarkt**: n Beschäftigte besitzen bereits einen festen Dauerparkplatz, jeder ordnet ALLE Plätze nach Entfernung zum eigenen Ziel (keine Reichweite, keine unvollständigen Listen wie in jedem bisherigen Stück). Top Trading Cycles findet die eindeutige **kernstabile** Zuordnung – und ist der einzige Mechanismus, der gleichzeitig Pareto-effizient, individuell-rational UND strategiefest ist (Ma 1994). Direkter algorithmischer Unterbau für [nierentausch-demo](https://github.com/sebastian-hanisch/nierentausch-demo), das letzte Stück der Linie – inzwischen ebenfalls gebaut.

```
greedy-matching-demo (Wurzel: eine gewählte Zuordnung bleibt)                     [gebaut]
  ├─ augmenting-path-demo … weighted-blossom-demo (Konvergenz)                    [gebaut]
  ├─ gale-shapley-demo (Vorlieben statt Kosten, stabil)                            [gebaut]
  │    ├─ stabile-mitbewohner-demo (eine Gruppe statt zwei Seiten)                 [gebaut]
  │    ├─ krankenhaus-zulassung-demo (many-to-one, Kapazitäten)                    [gebaut]
  │    └─ top-trading-cycles-demo (Tausch ohne Geld, Wohnungsmarkt)                [dieses Stück]
  │         └─ nierentausch-demo (Kompatibilität statt Präferenz, kurze Zyklen)    [gebaut]
  └─ online-matching-demo (Aufträge kommen nacheinander)                          [gebaut]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` über die 100 festen Karten (Seeds 100000–100099) belegt: 20 Personen, Vorlieben "Entfernung mit Streuung ±20 min", sofern nicht anders angegeben. Aufwand = **Listenvorrücken + Verfolgungsschritte**, nie Sekunden.

| Frage | Ergebnis |
|---|---|
| Tauschanteil | ✅ Im Mittel **78,8 %** tauschen tatsächlich (Median 80 %) – nur möglich, weil der Anfangsbesitz über einen von den Zielpunkten UNABHÄNGIGEN Zufallsstrom vergeben wird (siehe Negativbeispiel unten). |
| Gewinn für die Tauschenden | ✅ Im Mittel **9,2** Rangplätze besser (Median 9,0), Distanzgewinn im Mittel 31,3 Minuten (Median 29,0) – unter allen 20 Personen (inkl. Nicht-Tauschenden) Mittel 7,2/Median 7,0 Rangplätze bzw. Mittel 24,7/Median 21,0 Minuten. |
| Kreise je Karte | ✅ Im Mittel **9,1** Kreise (Median 9,0); Kreislängen gepoolt (907 Kreise über 100 Karten): 46,7 % Länge 1 (Selbstschleife), 22,7 % Länge 2, 13,1 % Länge 3, 17,4 % Länge ≥ 4 (höchste beobachtete Länge 11). |
| Verlorener Gewinn bei Längenbeschränkung | ⚠️ Nachträglich gefiltert (STRUKTURELLE Vorschau, keine neue Mechanik): bei Höchstlänge 2 gingen **76,6 %** des Distanzgewinns verloren, bei Höchstlänge 3 noch **54,3 %** – lange Kreise tragen weit überproportional bei. Motiviert Nierentausch (kurze Zyklen wegen Simultan-OPs), ist aber selbst keine Nierentausch-Zahl. |
| Individuelle Rationalität | ✅ **0 von 4.800** geprüften Personen-Instanzen (n ∈ {3,5,8,12,20} × 100 Karten) schlechter dran als mit dem eigenen Ausgangsplatz (Theorem, erschöpfend geprüft). |
| Strategiefestigkeit | ✅ **0 von 200** erschöpfend geprüften Falschmeldungen (5×5-Karten, alle 119 Permutationen je Person) verbessern das Ergebnis (Roth 1982). |
| Kern-Eindeutigkeit | ✅ **810 von 810** Kreuzprüfungen (n = 3–7, drei Vorliebenmodelle): der Kern besteht immer aus genau EINER Zuordnung, und sie ist immer TTCs Ergebnis (Roth & Postlewaite 1977). |
| Komplexität | ✅ Θ(n²) im schlechtesten Fall bewiesen: `Schritte / n²` = **1,0000** exakt für n = 10 bis 1280 an der Worst-Case-Karte (identische Präferenzliste, Identitätsbesitz). Auf der echten geometrischen Karte klar darunter (n=10→39,6, n=160→2.668,8, n=640→15.647,2 Schritte – empirisch, kein Beweis). |

## Was nicht funktioniert hat / widerlegte Vorab-Hypothesen

- **Die Zitat-Zuordnung war im ersten Entwurf falsch.** "TTC ist der einzige gleichzeitig Pareto-effiziente, individuell-rationale UND strategiefeste Mechanismus" stammt von **Ma (1994, *International Journal of Game Theory*)**, nicht von Roth (1982) – Roth (1982) zeigt nur, dass der Kern-Mechanismus selbst strategiefest IST, nicht dass er der einzige mit dieser Kombination ist. Die Kern-Eindeutigkeit (TTC = die einzige Kern-Allokation = die einzige walrasianische Allokation) stammt von **Roth & Postlewaite (1977, *JME*)**, nicht direkt von Shapley & Scarf (1974) selbst (die zeigen nur, dass der Kern nie leer ist). Alle drei Zitate im README und in der App sauber getrennt gehalten, statt zu einem Satz verkürzt.
- **Ohne unabhängigen Anfangsbesitz wäre die Demo inhaltlich tot.** Ein erster Modellierungsentwurf hätte den Anfangsbesitz an denselben Zufallsstrom wie die Zielpunkte gekoppelt (oder an den Index) – dann ist der eigene Platz für fast jeden trivial die beste Wahl, TTC besteht fast nur aus Selbstschleifen, und alle Tests würden trotzdem bestehen, ohne dass die Demo etwas zeigt. Gelöst durch einen eigenen, von der Punktziehung unabhängigen `SplitMix64`-Strom für die Anfangsbesitz-Permutation (analog `hr_scenario.py`s Kapazitätsvergabe) – UND ein bewusst gezeigtes Negativbeispiel (`😴 Kaum jemand tauscht`, Platz s liegt exakt auf Zielpunkt s), statt den Fehler nur stillschweigend zu vermeiden.
- **Die Komplexitätsangabe "O(n log n)" für den Basisfall ist nicht belegt.** Häufig kolportiert, aber die einzige im verfügbaren Material belegte Komplexitätsangabe betrifft eine Gleichstands-Variante, nicht den hier implementierten Fall mit strikten Präferenzen. Stattdessen eigens am Worst Case gemessen und bewiesen: Θ(n²), `Schritte/n²` exakt 1,0000 über drei Größenordnungen (n=10 bis 1280).
- **Die Besitzer-Invariante ist die fehleranfälligste Einzelstelle im Kern-Algorithmus.** `owner_of_slot` darf NIE auf den Empfänger eines Tauschs umgeschrieben werden – nur der ursprüngliche Besitzer entscheidet, ob ein Platz noch verfügbar ist. Eine naive Implementierung, die das nach jedem Kreis aktualisiert, würde in der Folgerunde falsche Ziele berechnen. Dieser Punkt ist als eigener, benannter Regressionstest geprüft (`test_owner_of_slot_is_never_rewritten_to_the_new_holder`), nicht nur implizit über Aggregatzahlen.

## Was die Demo zeigt

- **Suche und Ablauf:** Schritt-Slider und ▶️ über die Ereignisse (Zeiger rückt vor, Person zeigt auf ihren Favoriten, Kreis gefunden und aufgelöst): die Karte mit Zielpunkten (Kreise) und Plätzen (Quadrate); gepunktete graue Linie = aktueller Zeiger, dicke grüne Linie = abgeschlossener Tausch, lila = der zuletzt gefundene Kreis; am Ende der **Beweis** (gültige Zuordnung, individuelle Rationalität, kein blockierendes Zweiertausch-Paar).
- **Wer tauscht, wie viel bringt es?** Tauschanteil, Rang-/Distanzgewinn (alle vs. Tauschende), Kreislängen-Histogramm; Verteilung über 100 feste Karten.
- **Was, wenn nur kurze Kreise erlaubt wären?** Strukturelle Vorschau (Balkendiagramm) auf die Nierentausch-Frage, ohne neue Mechanik.
- **Lohnt sich Lügen?** Erschöpfende Manipulationsprobe (5×5-Karten, alle Permutationen).
- **Wovon hängt der Aufwand ab?** Aufwand gegen Größe (Worst Case Θ(n²) vs. echte geometrische Karte).
- **Feste Presets:** Lehrbuchkarte (zwei Runden) · Worst Case Θ(n²) · Mittlere Karte · Reichlich Rauschen · Nur Entfernung · Kleine Gruppe, ein langer Kreis · Kaum jemand tauscht (Negativbeispiel) · Beweis; **Wo die Annahmen enden.**

## Modell und Verfahren

- **Graph:** n Beschäftigte mit Zielpunkten, n Parkplätze auf derselben Karte (`SplitMix64`-Zufallsgenerator wie in allen Vorgängerdemos); **neu:** der Anfangsbesitz kommt aus einem eigenen, von den Punktkoordinaten unabhängigen Zufallsstrom (Fisher-Yates-Permutation). Keine Reichweite: jeder Platz ist für jeden erreichbar, die Präferenzlisten sind immer vollständig.
- **Top Trading Cycles (`tt_ttc.py`):** jede aktive Person zeigt auf die aktuelle Besitzerin ihres besten verbleibenden Platzes (`owner_of_slot`, FEST – nur der ursprüngliche Besitzer zählt, nie der Empfänger eines Tauschs). Kreissuche über 3-Farben-Markierung (unbesucht/auf dem Pfad/fertig); mehrere disjunkte Kreise können in derselben Runde gefunden werden. Terminiert immer in höchstens n Runden.
- **Kern-Stabilität:** keine Koalition kann durch internen Neu-Tausch ihrer eigenen Ausgangsgüter alle Mitglieder mindestens gleich und mindestens eines strikt besser stellen. Bei strikten Präferenzen ist der Kern nie leer (Shapley & Scarf 1974) und besteht aus genau einer Zuordnung – der TTC-Zuordnung (Roth & Postlewaite 1977).
- **In-App-Zertifikat vs. Orakel:** die App prüft nur notwendige, billige Bedingungen (Gültigkeit, individuelle Rationalität, kein blockierendes Zweiertausch-Paar); die vollständige, erschöpfende Kern-Stabilitätsprüfung über ALLE Koalitionsgrößen macht `tt_oracle.py` ausschließlich in den Tests (nur kleine n).

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `tt_constants.py` | Regler-Grenzen, Presets und Hilfetexte, feste Seed-Mengen |
| `tt_presets.py` | Permalink-, Preset- und Zufalls-Seed-Logik (`card_select` für die drei festen Karten) |
| `tt_scenario.py` | Karte (Zielpunkte, Plätze, **neu:** unabhängige Anfangsbesitz-Permutation), drei feste Karten (Lehrbuch, Worst Case, Negativbeispiel) |
| `tt_preferences.py` | Vollständige, strikte Vorlieben (nur Entfernung / Streuung / Zufall) |
| `tt_ttc.py` | **Neu:** der Kern-Algorithmus (Ereignisprotokoll, Zertifikat) |
| `tt_oracle.py` | **Neu:** Brute Force über alle Zuordnungen und Koalitionen (für Tests) |
| `tt_strategy.py` | **Neu:** erschöpfende Manipulationsprobe |
| `tt_evaluation.py` | Einordnung, Verteilung, Kreislängen, Längenbeschränkungs-Vorschau, Aufwand |
| `tt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Algorithmus (Kreuzprüfung gegen Brute Force, benannte Lehrbuchkarten-Regression, Besitzer-Invariante, Negativkontrolle, Strategiefestigkeit), Auswertung, Presets, belegte Zahlen, AppTest-Rauchtests |

Alle Daten sind synthetisch; die Laufzeit braucht nur numpy, pandas, plotly und streamlit.

## Lokal starten

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\streamlit run app.py
```

## Tests ausführen

```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest tests -v
```

Die Logik rechnet ausschließlich mit ganzen Zahlen; die im Text genannten Anteile und Mittelwerte sind deshalb auf jeder Plattform identisch.
Die CI (`.github/workflows/tests.yml`) läuft auf Ubuntu mit Python 3.12, bei jedem Push und wöchentlich mit den jeweils neuesten Bibliotheksversionen.
