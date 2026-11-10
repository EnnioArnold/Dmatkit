# dmatkit

Diskrete Mathematik mit nachvollziehbarem Rechenweg, gebaut zum Modul
DMATH-ALGO der HSLU (Diskrete Mathematik für Datenstrukturen und Algorithmen).
Deckt die Semesterwochen 1 bis 9 ab: Elementare Datentypen, Aussagenlogik,
Prädikatenlogik, Beweiskalkül, Analyse von Algorithmen, rekursive Algorithmen,
mathematische Induktion, Zähltechniken und komplexere Zähltechniken. Schwesterprojekt von
[lialkit](https://github.com/EnnioArnold/lialkit) (Lineare Algebra) und
[anakit](https://github.com/EnnioArnold/Analysiskit) (Analysis).

Die Modulendprüfung läuft 90 Minuten auf Papier. Darum zeigt dmatkit jeden
Schritt so, wie er auf dem Blatt stünde, und nennt die Regel dazu. Aufgaben mit
Programmieranteil gibt es als Gerüst mit Prüfstand statt als Musterlösung.

## Installieren

Als Paket (Notebook und App in einem):

```bash
pip3 install git+https://github.com/EnnioArnold/dmatkit
python3 -m dmatkit        # öffnet die Qt-App (auch: dmatkit)
```

Im Notebook dann `import dmatkit as dk`. Mit `pip3 install "dmatkit[anim] @ git+https://github.com/EnnioArnold/dmatkit"` kommt manimgx dazu.

Oder ohne Installation, aus dem Ordner:

Nötig ist nur Python mit SymPy. Für Zeichnungen und Fenster kommt dazu:

```bash
pip install -r requirements.txt      # sympy, numpy, matplotlib, plotly, PySide6
pip install manimgx                  # Animationen, freiwillig (Python 3.13+)
```

manimgx rendert auf der GPU und schreibt das MP4 ohne ffmpeg. Als Rückfall
geht Manim CE (`brew install cairo pango pkg-config ffmpeg`, `pip install manim`).
Die Videos kommen im Look der App: heller Canvas, Tinte, weiche Pastell-Orbs. Beispiel:
`python3 -m dmatkit.grafik.anim 409` rendert die Umwandlung 409 → Binär.

Der Ordner `dmatkit/` liegt neben deinen Wochen-Ordnern. Aus einem Notebook in
`Week 3/` heraus:

```python
import sys
sys.path.insert(0, '..')
import dmatkit as dk

dk.eval_bool("False or True and False and True or False")    # SW1: Vorrang, Schritt für Schritt
dk.to_binary(409)                                            # SW1: 110011001
dk.truth_table("(A or B) and not C")                         # SW2: Wahrheitstabelle
dk.check_equivalence("A -> B", "not B -> not A")             # SW2: Kontraposition
dk.has_duplicate([3, 1, 4, 1, 5])                            # SW3: ∃i ∃j, mit Zeuge
dk.entails(["A -> B", "A"], "B")                             # SW4: drei Prüfmethoden
dk.resolution(["A -> B", "B -> C"], "A -> C")                # SW4: Resolution mit Graph
dk.count_steps("decToBin", x=25)                             # SW5: Rechenschritte zählen
dk.max_input_size("n**2", time_limit_s=60)                   # SW5: grösstes n in einer Minute
dk.recursion_tree("mergeSort", [4, 6, 5, 1, 7, 4, 3, 1])     # SW6: Rekursionsbaum
dk.master_theorem(2, 2, 1)                                   # SW6: T(n) = 2T(n/2) + n  ->  Θ(n log n)
dk.solve_recurrence([6, -9], 0, {0: 1, 1: 6})                # SW6: T(n) = 6T(n−1) − 9T(n−2)  ->  (1 + n)·3ⁿ
dk.count_divisible(100000, [2, 3, 5, 7])                     # SW9: Inklusion und Exklusion  ->  77143
dk.count_recursive("stairs", 10)                             # SW9: Treppe mit 10 Stufen, s(n) = s(n−1) + s(n−2)  ->  89
dk.gf_coins([1, 2, 5], 15, ordered=True)                     # SW9: erzeugende Funktion  ->  1843 Folgen
```

Formeln schreibst du wie im Unterricht: `and or not xor -> <->` oder mit
Symbolen `∧ ∨ ¬ ⊕ → ↔`. Vorrang: not vor and vor xor vor or vor `->` (rechts
geklammert) vor `<->`. Jedes Ergebnis zeigt sich im Notebook von selbst;
`.latex()` liefert den Rechenweg für eine Abgabe, `dk.info()` listet alle
Funktionen auf.

## Aufbau

![Notebook und Fenster rechnen mit demselben Modul](docs/architektur.svg)

```
app/        das Fenster (dmatkit_qt.py)
rechnen/    Rechenkern: core (Formelbaum, Parser), render (Rechenweg, Tabellen)
            und je Semesterwoche ein Modul:
              datentypen     SW1  Booleans, Ganzzahlen, Binär, IEEE 754, Mengen
              aussagenlogik  SW2  Wahrheitstabellen, Gesetze, Normalformen, Syntaxbaum
              praedikate     SW3  Prädikate, ∀ und ∃, Negation, Listen-Aufgaben
              kalkuel        SW4  Folgerung ⊨, Ableitung ⊢, KNF, Resolution
              algorithmen    SW5  Rechenschritte zählen, Worst Case, Landau
              rekursion      SW6  Rekursionsbaum, Hanoi, Master-Satz, lineare Rekursionen
              induktion      SW7  schwache und starke Induktion, Parkettierung, Münzen, quickSort
              zaehlen        SW8  Summen-, Produkt-, Zuordnungsregel, sechs Zählprobleme, IPv4-Teilnetz
              zaehlkomplex   SW9  Inklusion und Exklusion, Zählen mit Rekursion, erzeugende Funktionen
grafik/     Zeichnungen (plots)
aufgaben/   Übungsaufgaben der Serien 1–9 (exercises), Prüfstände zum Selbstprogrammieren (uebung)
docs/       Architektur-Diagramm
tests/      ein Testskript je Modul
```

## Sicherheit und Genauigkeit

Eingaben werden nie mit `eval` ausgeführt: Formeln liest ein eigener Parser,
arithmetische Terme und Python-Ausdrücke laufen über eine Positivliste auf dem
AST, der Schrittzähler für Algorithmen ist ein eigener Interpreter mit
Schritt- und Tiefenlimit. Gerechnet wird exakt (ganze Zahlen, SymPy-Brüche).

Rechnet dmatkit anders als eine Folie, steht das im Rechenweg oder im Docstring.
Aufgefallen sind zum Beispiel: in der Mitschrift zu 409 steht »204 = 102 · 1 + 0«
(richtig: · 2), `decToBin(0)` liefert in den Folien die leere Zeichenkette, und
die Lerngerüst-Aufgabe `0.0(110)` ergibt 3/7 statt 3/14.

## Die Übungsaufgaben

```python
from dmatkit.exercises import liste, aufgabe, loesen, pruefen, alle_pruefen

liste(3)              # welche es in SW3 gibt
aufgabe("SW3.2")      # die Angabe
loesen("SW3.2")       # durchgerechnet, mit Rechenweg
alle_pruefen()        # alle Aufgaben gegen die erwarteten Werte
```

**Zum Selbstprogrammieren** gibt es Prüfstände ohne Musterlösung:

```python
from dmatkit.uebung import vorlage, pruefe_dec_to_bin

print(vorlage("dec_to_bin"))        # Gerüst zum Abschreiben

def meine_dec_to_bin(n):
    ...

pruefe_dec_to_bin(meine_dec_to_bin)
```

## Design

App, Zeichnungen und Animationen teilen sich ein Design, das `design.py` zentral
festlegt (Farben, Radien, Schriften, Abstände). Vorlage ist eine unabhängige Analyse
des ElevenLabs-Designsystems (Quelle: getdesign.md, DESIGN.md), keine Kopie.

- Heller Off-White-Canvas `#f5f5f5`, warme Tinte `#292524`, weisse Karten mit 1px Hairline
  und Radius 16, Pillen-Buttons (primär Tinte, sekundär Outline), Eingaben mit Radius 8.
- Keine gesättigte Akzentfarbe. Pastell-Orbs (mint, peach, lavender, sky, rose) sind nur
  Atmosphäre hinter Seitenkopf und leeren Zuständen. Wahr/Falsch und die Markierungen
  im Rechenweg bleiben grün/rot, gedämpft als Flächen.
- Dunkel: Tinten-Canvas `#0c0a09` mit Karten in `#1c1917`.
- Schriften: Inter für die Oberfläche, EB Garamond Light als Ersatz für die Display-Schrift
  Waldenburg, Monospace für Code. Es liegen keine Schriftdateien im Repo; fehlt eine
  Schrift, greift ein Rückfall (System-Sans, Georgia/Times).

## Das Fenster

```bash
cd dmatkit                       # Ordnername ist egal
pip install -r requirements.txt  # einmalig
python3 app/dmatkit_qt.py
```

Neun Seiten, eine je Semesterwoche. Jedes Ergebnis zeigt **Rechenweg** und
**Zeichnung**. Die Prüfung über Wolfram|Alpha ist optional und braucht eine
kostenlose AppID von <https://developer.wolframalpha.com/> (Umgebungsvariable
`WOLFRAM_APPID` oder einmalige Eingabe in der App).

Die Zeichnungen (`plot_*`) sind matplotlib-Figuren, `dark=True` schaltet den
Dunkelmodus ein, `plotly_growth` öffnet Wachstumskurven interaktiv.

## Tests

```bash
python3 tests/tests_datentypen.py     # ebenso aussagenlogik, praedikate, kalkuel,
python3 tests/tests_algorithmen.py    # algorithmen, rekursion, induktion, zaehlen, zaehlkomplex, plots, exercises, uebung, app
```

## Noch nicht enthalten

SW10 bis SW12 (Relationen, Graphentheorie und weitere Themen) sind noch nicht behandelt. Der Aufbau ist darauf
ausgelegt: ein neues Modul in `rechnen/`, seine Namen in `__init__.py`, ein Testskript.

Zu SW7 bis SW9 enthalten die Unterlagen nur die Aufgabenstellungen. Die Lösungen sind eigene Rechnungen
(in `exercises` als »Lösung eigen« gekennzeichnet) und gegen unabhängige Python-Rechnungen geprüft; Unklares steht als TODO
in den Docstrings von `rechnen/induktion.py`, `rechnen/zaehlen.py` und `rechnen/zaehlkomplex.py`
(SW9: Länge n in Aufgabe 8 nicht genannt, darum Parameter; Deutung von »Inklusion« und »Exklusion« nach Seite 3 der Serie).
