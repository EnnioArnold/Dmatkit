#!/usr/bin/env python3
"""
Komplexere Zähltechniken (Semesterwoche 9, Serie 9).

Was hier steht (alles exakt mit ganzen Zahlen gerechnet; wo es klein genug ist, wird jedes Ergebnis
zusätzlich durch Aufzählen aller Möglichkeiten geprüft):

  Frage 1: Inklusion und Exklusion
    inclusion_exclusion(sets)            |S₁ ∪ … ∪ Sₙ| = Summe + Inklusion − Exklusion, mit Probe durch Vereinigen
    count_divisible(limit, divisors)     Zahlen von 1 bis limit, die durch eine der Zahlen teilbar sind (Aufgaben 2 bis 4)
    count_fixed_point(n)                 Vertauschungen von n Buchstaben mit mindestens einem festen Platz (Aufgabe 5)
    count_unused(n, m)                   n Aufträge auf m Drucker, mindestens ein Drucker frei (Aufgabe 6)

  Frage 2: Zählen mit Rekursion (divide and conquer)
    count_recursive(problem, n)          s(n) über eine Rekursionsbeziehung (Aufgaben 7 bis 11):
                                         "no00", "even_zeros", "no000", "contains01", "stairs"

  Frage 3: Zählen mit erzeugenden Funktionen
    gf_count(factors, target)            Koeffizient von xᵗ im Produkt der Faktoren (Beispiel Seite 12, Aufgaben 12, 13)
    gf_coins(coins, target, ordered)     Münzen zu einem Betrag, ohne oder mit Reihenfolge (Aufgabe 14)

Hinweise zu den Unterlagen:
  * Die PDF-Serie 9 enthält nur die Aufgabenstellungen, keine Lösungen. Alle Resultate sind eigene Rechnungen,
    gegen unabhängige Aufzählungen geprüft.
  * Die Serie definiert »Summe«, »Inklusion« und »Exklusion« (Seite 3). Hier gilt: Summe = Einzelmengen,
    Exklusion = Schnitte einer geraden, Inklusion = Schnitte einer ungeraden Zahl ≥ 3 von Mengen. Damit stimmt das
    Beispiel auf Seite 2 (12 + 1 − 6 = 7).
  * Aufgabe 5 und 6 sind als Siebformel (Inklusion/Exklusion mit gleich grossen Schnitten) gelöst; die Serie
    gibt nur den Hinweis auf die Zerlegung S₁ ∪ … ∪ Sₙ.
  * Aufgabe 8 liest »gerade Anzahl Nullen« als Ziffernwörter der Länge n (die Null ist gerade, also zählt »keine Null«
    mit). TODO: Länge n ist in der Aufgabe nicht genannt; die Länge ist ein Parameter.
  * Aufgabe 14 b (»der Reihe nach einwerfen«): geordnete Münzfolgen; ohne Reihenfolge (a) zählt nur, wie oft jede Münze vorkommt.
  * Aufgabe 10: »enthält das Muster 01« als Teilwort an beliebiger Stelle, nicht nur am Anfang.
"""

from __future__ import annotations

import itertools
import math

from .render import Result, Step, Table
from .zaehlen import CountResult, _fmt, _int

# ==========================================================================
# Grenzen
# ==========================================================================

MAX_SETS = 12                  # Mengen bei Inklusion/Exklusion (2ⁿ Schnitte)
MAX_BRUTE = 200_000            # so viele Möglichkeiten werden höchstens zur Probe aufgezählt
MAX_FACTORS = 40
MAX_TARGET = 5000

__all__ = ["GFResult", "inclusion_exclusion", "count_divisible", "count_fixed_point", "count_unused",
           "count_recursive", "RECURSIVE_PROBLEMS", "gf_count", "gf_coins"]

_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _pow(e: int) -> str:
    return "x" if e == 1 else ("1" if e == 0 else "x" + str(e).translate(_SUP))


def _poly(exps) -> str:
    return " + ".join(_pow(e) for e in exps)


# ==========================================================================
# Frage 1: Inklusion und Exklusion
# ==========================================================================

def _ie_steps(res: CountResult, n: int, rows: list[list], summe: int, inklusion: int, exklusion: int):
    """Die vier Schritte der Serie (Seite 3) als Rechenweg. rows: [k, Anzahl Schnitte, Summe der Grössen]."""
    res.steps.append(Step("Summe", "Anzahl Elemente in allen Mengen S₁, …, Sₙ zusammenzählen.", items=[("Summe", _fmt(summe))], rule="Inklusion und Exklusion"))
    res.steps.append(Step("Schnitte", "Alle Überschneidungen von k Mengen: Anzahl der Schnitte und die Summe ihrer Grössen.",
                          table=Table(["k Mengen", "Anzahl Schnitte", "Summe der Grössen", "zählt zu"],
                                      [[str(k), str(c), _fmt(s), "Summe" if k == 1 else ("Exklusion" if k % 2 == 0 else "Inklusion")] for k, c, s in rows])))
    res.steps.append(Step("Exklusion", "Schnitte einer geraden Anzahl von Mengen.", items=[("Exklusion", _fmt(exklusion))], rule="Inklusion und Exklusion"))
    res.steps.append(Step("Inklusion", "Schnitte einer ungeraden Anzahl (≥ 3) von Mengen.", items=[("Inklusion", _fmt(inklusion))], rule="Inklusion und Exklusion"))
    res.steps.append(Step("Ergebnis", "|S| = Summe + Inklusion − Exklusion",
                          items=[("|S|", f"{_fmt(summe)} + {_fmt(inklusion)} − {_fmt(exklusion)} = {_fmt(res.count)}")], rule="Inklusion und Exklusion"))
    res.summe, res.inklusion, res.exklusion = summe, inklusion, exklusion


def _split(rows):
    """Aus Zeilen [k, Anzahl, Summe der Grössen] die drei Teile der Regel."""
    summe = rows[0][2]
    exk = sum(s for k, _, s in rows if k % 2 == 0)
    ink = sum(s for k, _, s in rows if k % 2 == 1 and k >= 3)
    return summe, ink, exk


def inclusion_exclusion(sets) -> CountResult:
    """
    Prinzip von Inklusion und Exklusion (Serie 9, Frage 1): |S₁ ∪ … ∪ Sₙ| = Summe + Inklusion − Exklusion.
    ``sets`` ist eine Liste von Mengen (beliebige Iterables). Zur Probe wird die Vereinigung direkt gezählt.

    >>> inclusion_exclusion([{1, 4, 5, 7}, {2, 4, 6, 7}, {3, 5, 6, 7}]).count
    7
    """
    ss = [frozenset(s) for s in sets]
    if not 1 <= len(ss) <= MAX_SETS:
        raise ValueError(f"Es braucht 1 bis {MAX_SETS} Mengen")
    n = len(ss)
    rows = []
    for k in range(1, n + 1):
        sizes = [len(frozenset.intersection(*c)) for c in itertools.combinations(ss, k)]
        rows.append([k, len(sizes), sum(sizes)])
    summe, ink, exk = _split(rows)
    res = CountResult()
    res.count = summe + ink - exk
    res.formula = f"{summe} + {ink} − {exk}"
    res.title = f"Inklusion und Exklusion: {n} Mengen, |S| = {_fmt(res.count)}"
    res.summary = f"Die Vereinigung hat {_fmt(res.count)} Elemente."
    res.steps.append(Step("Idee", "Elemente in mehreren Mengen werden von der Summe mehrfach gezählt: erst zu viel, dann zu viel abgezogen, dann wieder zugefügt.",
                          rule="Inklusion und Exklusion"))
    _ie_steps(res, n, rows, summe, ink, exk)
    if len(frozenset().union(*ss)) != res.count:
        raise AssertionError("Vereinigung weicht von der Formel ab")                 # nie erwartet
    res.checked = True
    res.steps.append(Step("Probe", "Die Vereinigung direkt gezählt stimmt überein.", items=[("|S₁ ∪ … ∪ Sₙ|", len(frozenset().union(*ss)))]))
    return res._finish("|S|")


def count_divisible(limit: int, divisors) -> CountResult:
    """
    Wie viele Zahlen von 1 bis ``limit`` sind durch (mindestens) eine der Zahlen ``divisors`` teilbar?
    Menge Sᵢ = Vielfache von dᵢ, |Sᵢ| = ⌊limit/dᵢ⌋; ein Schnitt hat das kleinste gemeinsame Vielfache als Schritt.
    Das Gegenteil (durch keine teilbar) steht in ``complement`` (Aufgabe 3: der else-Zweig).

    >>> count_divisible(1000, [2, 3, 5]).count
    734
    >>> count_divisible(100000, [2, 3, 5, 7]).count
    77143
    """
    lim = _int(limit, "limit", 1, 10 ** 12)
    ds = [_int(d, "Teiler", 1, 10 ** 9) for d in divisors]
    if not 1 <= len(ds) <= MAX_SETS:
        raise ValueError(f"Es braucht 1 bis {MAX_SETS} Teiler")
    rows = []
    for k in range(1, len(ds) + 1):
        sizes = [lim // math.lcm(*c) for c in itertools.combinations(ds, k)]
        rows.append([k, len(sizes), sum(sizes)])
    summe, ink, exk = _split(rows)
    res = CountResult()
    res.count = summe + ink - exk
    res.complement = lim - res.count
    res.formula = f"{summe} + {ink} − {exk}"
    teiler = ", ".join(map(str, ds))
    res.title = f"Zahlen von 1 bis {_fmt(lim)}, teilbar durch {teiler}: {_fmt(res.count)}"
    res.summary = f"{_fmt(res.count)} Zahlen sind teilbar, {_fmt(res.complement)} nicht."
    res.steps.append(Step("Mengen", f"Sᵢ = Vielfache von dᵢ in 1, …, {_fmt(lim)}; |Sᵢ| = ⌊{_fmt(lim)} / dᵢ⌋. Ein Schnitt Sᵢ ∩ Sⱼ ∩ … sind die Vielfachen "
                          "des kleinsten gemeinsamen Vielfachen (bei Primzahlen das Produkt).",
                          items=[(f"|S({d})|", lim // d) for d in ds], rule="Inklusion und Exklusion"))
    _ie_steps(res, len(ds), rows, summe, ink, exk)
    res.steps.append(Step("Gegenteil", f"Durch keine der Zahlen teilbar: {_fmt(lim)} − {_fmt(res.count)}.", items=[("nicht teilbar", _fmt(res.complement))], rule="Gegenteil zählen"))
    if lim <= MAX_BRUTE:
        got = sum(1 for m in range(1, lim + 1) if any(m % d == 0 for d in ds))
        if got != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Alle Zahlen 1 bis {_fmt(lim)} durchgegangen: gleiches Ergebnis."))
    return res._finish()


def _symmetric(res: CountResult, n: int, size_k, what: str, label: str):
    """Siebformel, wenn alle Schnitte von k Mengen gleich gross sind: Σ (−1)^(k+1)·C(n, k)·size_k(k)."""
    rows = [[k, math.comb(n, k), math.comb(n, k) * size_k(k)] for k in range(1, n + 1)]
    summe, ink, exk = _split(rows)
    res.count = summe + ink - exk
    res.steps.append(Step("Zerlegung", f"S = S₁ ∪ … ∪ S{str(n).translate(str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉'))}, Sᵢ = {what}. Die Mengen überlappen sich, "
                          "darum Inklusion und Exklusion. Ein Schnitt von k Mengen hat überall dieselbe Grösse, es gibt C(n, k) davon (Produktregel).",
                          rule="Inklusion und Exklusion"))
    res.steps.append(Step("Grösse eines Schnitts", label,
                          table=Table(["k", "C(n, k)", "Grösse eines Schnitts", "Beitrag"],
                                      [[str(k), str(math.comb(n, k)), _fmt(size_k(k)), ("+" if k % 2 else "−") + _fmt(math.comb(n, k) * size_k(k))] for k in range(1, n + 1)]),
                          rule="Produktregel"))
    _ie_steps(res, n, rows, summe, ink, exk)


def count_fixed_point(n: int) -> CountResult:
    """
    Vertauschungen (Permutationen) von n verschiedenen Buchstaben, bei denen mindestens ein Buchstabe am gleichen Platz
    steht (Serie 9, Aufgabe 5, COMPUTER: n = 8). Sᵢ = Vertauschungen, in denen der i-te Buchstabe fest bleibt; ein Schnitt
    von k Mengen hat (n−k)! Elemente. Das Gegenteil (kein fester Platz) ist ``complement``.

    >>> count_fixed_point(8).count
    25487
    """
    n = _int(n, "n", 1, 400)
    res = CountResult()
    res.title = f"{n} Buchstaben vertauschen, mindestens einer am gleichen Platz"
    _symmetric(res, n, lambda k: math.factorial(n - k), f"Vertauschungen, in denen der i-te Buchstabe am Platz bleibt, |Sᵢ| = (n−1)!",
               f"Halten k Buchstaben ihren Platz, ordnen sich die übrigen n−k frei an: (n−k)! = ({n}−k)!.")
    res.complement = math.factorial(n) - res.count
    res.formula = "Σ (−1)^(k+1)·C(n, k)·(n−k)!"
    res.summary = f"{_fmt(res.count)} von {_fmt(math.factorial(n))} Vertauschungen; {_fmt(res.complement)} haben keinen festen Platz."
    res.steps.append(Step("Gegenteil", f"Ohne festen Platz: {n}! − {_fmt(res.count)}.", items=[("ohne festen Platz", _fmt(res.complement))], rule="Gegenteil zählen"))
    if n <= 8:
        got = sum(1 for p in itertools.permutations(range(n)) if any(p[i] == i for i in range(n)))
        if got != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Alle {math.factorial(n)} Vertauschungen durchgegangen: gleiches Ergebnis."))
    return res._finish()


def count_unused(n: int, m: int) -> CountResult:
    """
    n verschiedene Aufträge auf m verschiedene Drucker verteilen, so dass mindestens ein Drucker frei bleibt
    (Serie 9, Aufgabe 6: n = 7, m = 5). Sᵢ = Verteilungen, in denen Drucker i frei bleibt, |Sᵢ| = (m−1)ⁿ; ein Schnitt
    von k Mengen hat (m−k)ⁿ Elemente. Das Gegenteil (alle belegt) ist ``complement`` und stimmt mit
    ``count_surjections(n, m)`` überein.

    >>> count_unused(7, 5).count
    61325
    """
    n, m = _int(n, "n", 0, 400), _int(m, "m", 1, 200)
    res = CountResult()
    res.title = f"{n} Aufträge auf {m} Drucker, mindestens ein Drucker frei"
    _symmetric(res, m, lambda k: (m - k) ** n, "Verteilungen, in denen Drucker i frei bleibt, |Sᵢ| = (m−1)ⁿ",
               f"Bleiben k Drucker frei, wählt jeder Auftrag unter den übrigen {m}−k Druckern: ({m}−k)^{n}.")
    res.complement = m ** n - res.count
    res.formula = "Σ (−1)^(k+1)·C(m, k)·(m−k)^n"
    res.summary = f"{_fmt(res.count)} von {_fmt(m ** n)} Verteilungen; in {_fmt(res.complement)} sind alle Drucker belegt."
    res.steps.append(Step("Gegenteil", f"Alle Drucker belegt: {m}^{n} − {_fmt(res.count)} (das sind die Verteilungen ohne leeres Fach).",
                          items=[("alle belegt", _fmt(res.complement))], rule="Gegenteil zählen"))
    if m ** n <= MAX_BRUTE:
        got = sum(1 for f in itertools.product(range(m), repeat=n) if len(set(f)) < m)
        if got != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Alle {m}^{n} = {_fmt(m ** n)} Verteilungen durchgegangen: gleiches Ergebnis."))
    return res._finish()


# ==========================================================================
# Frage 2: Zählen mit Rekursion
# ==========================================================================

class _Problem:
    def __init__(self, title, what, rec, init, step, why, closed, closed_fn, brute, brute_max):
        self.title, self.what, self.rec, self.init, self.step = title, what, rec, init, step
        self.why, self.closed, self.closed_fn = why, closed, closed_fn
        self.brute, self.brute_max = brute, brute_max


def _bin(n):
    return itertools.product("01", repeat=n)


def _stairs(n):
    """Alle Schrittfolgen aus 1 und 2 mit Summe n (ohne Formel, rekursiv aufgeschrieben)."""
    if n == 0:
        yield ()
        return
    for s in (1, 2):
        if s <= n:
            for rest in _stairs(n - s):
                yield (s,) + rest


def _fib(k):
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a


RECURSIVE_PROBLEMS = {
    "no00": _Problem(
        "Datenworte der Länge n ohne zwei aufeinanderfolgende Nullen (Aufgabe 7)",
        "Datenworte der Länge n ohne »00«",
        "s(n) = s(n−1) + s(n−2)", {1: 2, 2: 3},
        lambda s, n: s[n - 1] + s[n - 2],
        "Letztes Bit 1: davor ein beliebiges gültiges Wort der Länge n−1 → s(n−1). Letztes Bit 0: dann muss davor eine 1 stehen, davor ein gültiges Wort der "
        "Länge n−2 → s(n−2). Verankerung: s(1) = 2 (0, 1), s(2) = 3 (01, 10, 11).",
        "F(n+2) (Fibonacci-Zahlen, F(1) = F(2) = 1)", lambda n: _fib(n + 2),
        lambda n: sum(1 for w in _bin(n) if "00" not in "".join(w)), 17),
    "even_zeros": _Problem(
        "Passwörter aus Ziffern der Länge n mit gerader Anzahl Nullen (Aufgabe 8)",
        "Ziffernwörter der Länge n mit gerader Anzahl Nullen (0 Nullen zählt mit)",
        "s(n) = 8·s(n−1) + 10ⁿ⁻¹", {1: 9},
        lambda s, n: 8 * s[n - 1] + 10 ** (n - 1),
        "Letzte Ziffer ≠ 0 (9 Möglichkeiten): davor ein Wort mit gerader Anzahl Nullen → 9·s(n−1). Letzte Ziffer 0: davor ein Wort mit ungerader "
        "Anzahl Nullen, das sind alle 10ⁿ⁻¹ ohne die s(n−1) geraden → 10ⁿ⁻¹ − s(n−1). Zusammen 8·s(n−1) + 10ⁿ⁻¹. Verankerung: s(1) = 9 (Ziffern 1 bis 9).",
        "(10ⁿ + 8ⁿ) / 2", lambda n: (10 ** n + 8 ** n) // 2,
        lambda n: sum(1 for w in itertools.product("0123456789", repeat=n) if w.count("0") % 2 == 0), 5),
    "no000": _Problem(
        "Datenworte der Länge n ohne drei benachbarte Nullen (Aufgabe 9)",
        "Datenworte der Länge n ohne »000«",
        "s(n) = s(n−1) + s(n−2) + s(n−3)", {1: 2, 2: 4, 3: 7},
        lambda s, n: s[n - 1] + s[n - 2] + s[n - 3],
        "Das Wort endet auf 1, 10 oder 100 (nie auf 000). Davor steht ein gültiges Wort der Länge n−1, n−2 bzw. n−3. Verankerung: s(1) = 2, s(2) = 4, "
        "s(3) = 8 − 1 = 7 (nur 000 fehlt).",
        "Tribonacci-artig, keine einfache Formel (Charakteristische Gleichung x³ = x² + x + 1)", None,
        lambda n: sum(1 for w in _bin(n) if "000" not in "".join(w)), 17),
    "contains01": _Problem(
        "Datenworte der Länge n, die das Muster 01 enthalten (Aufgabe 10)",
        "Datenworte der Länge n, die »01« als Teilwort enthalten",
        "t(n) = 2·t(n−1) + (n−1)", {1: 0},
        lambda s, n: 2 * s[n - 1] + (n - 1),
        "Erstes Bit 1: der Rest muss »01« enthalten → t(n−1). Erstes Bit 0: der Rest enthält »01«, oder er beginnt mit 1 (dann entsteht »01« vorn); Worte ohne »01« "
        "haben die Form 1ᵃ0ᵇ, mit a ≥ 1 sind das n−1 Worte → t(n−1) + (n−1). Zusammen 2·t(n−1) + (n−1). Verankerung: t(1) = 0.",
        "2ⁿ − (n + 1)", lambda n: 2 ** n - (n + 1),
        lambda n: sum(1 for w in _bin(n) if "01" in "".join(w)), 17),
    "stairs": _Problem(
        "Möglichkeiten, eine Treppe mit n Stufen hochzusteigen (1 oder 2 Stufen pro Schritt) (Aufgabe 11)",
        "Schrittfolgen aus 1 und 2 mit Summe n",
        "s(n) = s(n−1) + s(n−2)", {1: 1, 2: 2},
        lambda s, n: s[n - 1] + s[n - 2],
        "Der letzte Schritt ist 1 (davor eine Treppe mit n−1 Stufen) oder 2 (davor n−2). Verankerung: s(1) = 1, s(2) = 2 (1+1, 2).",
        "F(n+1) (Fibonacci-Zahlen)", lambda n: _fib(n + 1),
        lambda n: sum(1 for _ in _stairs(n)), 25),
}


class RecursionResult(CountResult):
    """``values`` (n → s(n)), ``recurrence`` (Text), ``closed`` (Text der geschlossenen Form oder None)."""
    values = None
    recurrence = ""
    closed = ""


def count_recursive(problem: str, n: int) -> RecursionResult:
    """
    Zählen mit divide and conquer (Serie 9, Frage 2): s(n) bestimmen, Rekursionsbeziehung aufstellen, bis n ausrechnen.
    ``problem`` ist einer von ``RECURSIVE_PROBLEMS``: "no00" (Aufgabe 7), "even_zeros" (8), "no000" (9), "contains01" (10),
    "stairs" (11).

    >>> count_recursive("no00", 5).count
    13
    >>> count_recursive("stairs", 10).count
    89
    """
    if problem not in RECURSIVE_PROBLEMS:
        raise ValueError(f"Unbekanntes Problem {problem!r}. Möglich: {', '.join(RECURSIVE_PROBLEMS)}")
    p = RECURSIVE_PROBLEMS[problem]
    n = _int(n, "n", 1, 2000)
    s = dict(p.init)
    for k in range(max(p.init) + 1, n + 1):
        s[k] = p.step(s, k)
    res = RecursionResult()
    res.values, res.recurrence, res.closed = s, p.rec, p.closed
    res.count = s[n]
    res.formula = p.rec
    res.title = f"{p.title}: n = {n}"
    res.summary = f"s({n}) = {_fmt(res.count)}"
    res.steps.append(Step("Modellieren", f"s(n) = Anzahl der {p.what}.", rule="divide and conquer"))
    res.steps.append(Step("Rekursionsbeziehung", p.why, items=[("Rekursion", p.rec), ("Verankerung", ", ".join(f"s({k}) = {v}" for k, v in p.init.items()))],
                          rule="divide and conquer"))
    shown = list(range(1, min(n, 12) + 1))
    res.steps.append(Step("Werte ausrechnen", "Die Rekursion von der Verankerung aus anwenden.",
                          table=Table(["n"] + [str(k) for k in shown], [["s(n)"] + [_fmt(s[k]) for k in shown]]),
                          items=[(f"s({n})", _fmt(res.count))]))
    if p.closed_fn is not None:
        if any(p.closed_fn(k) != s[k] for k in range(1, min(n, 300) + 1)):
            raise AssertionError("geschlossene Form weicht von der Rekursion ab")   # nie erwartet
        res.steps.append(Step("Geschlossene Form", f"Aufgelöst: s(n) = {p.closed}.", items=[(f"s({n})", _fmt(p.closed_fn(n)))], rule="Rekursionsbeziehung auflösen"))
    else:
        res.steps.append(Step("Geschlossene Form", f"Hier genügt die Rekursion; {p.closed}."))
    if n <= p.brute_max:
        got = p.brute(n)
        if got != res.count:
            raise AssertionError("Aufzählung weicht von der Rekursion ab")          # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Alle Möglichkeiten für n = {n} aufgezählt: {_fmt(got)}, stimmt."))
    return res._finish(f"s({n})")


# ==========================================================================
# Frage 3: Zählen mit erzeugenden Funktionen
# ==========================================================================

class GFResult(CountResult):
    """``poly`` (Exponent → Koeffizient des ausmultiplizierten Produkts, bei Münzen bis zum Betrag), ``target`` (der gesuchte Exponent)."""
    poly = None
    target = 0


def _mul(a: dict, b: dict, cap: int | None = None) -> dict:
    out: dict = {}
    for i, x in a.items():
        for j, y in b.items():
            if cap is None or i + j <= cap:
                out[i + j] = out.get(i + j, 0) + x * y
    return out


def _poly_table(poly: dict, target: int) -> Table | None:
    keys = sorted(poly)
    if len(keys) > 40:
        keys = [k for k in keys if abs(k - target) <= 5]
    return Table(["Potenz"] + [_pow(k) for k in keys], [["Koeffizient"] + [_fmt(poly[k]) for k in keys]])


def gf_count(factors, target: int) -> GFResult:
    """
    Anzahl Lösungen von x₁ + … + xₙ = target, wenn xᵢ in der Menge ``factors[i]`` liegt (Serie 9, Frage 3).
    Erzeugende Funktion (xᵃ + xᵇ + …)·(…)·…; der Koeffizient von x^target ist die Antwort.

    >>> gf_count([[2, 3, 4], [3, 4], [4, 5]], 11).count
    4
    >>> gf_count([range(1, 7)] * 4, 13).count
    140
    """
    if not 1 <= len(factors) <= MAX_FACTORS:
        raise ValueError(f"Es braucht 1 bis {MAX_FACTORS} Faktoren")
    t = _int(target, "target", 0, MAX_TARGET)
    sets = [sorted(set(_int(e, "Exponent", 0, MAX_TARGET) for e in f)) for f in factors]
    if any(not f for f in sets):
        raise ValueError("Jeder Faktor braucht mindestens einen erlaubten Wert")
    poly: dict = {0: 1}
    for f in sets:
        poly = _mul(poly, {e: 1 for e in f})
    res = GFResult()
    res.poly, res.target = poly, t
    res.count = poly.get(t, 0)
    res.formula = " · ".join(f"({_poly(f)})" for f in sets) if len(sets) <= 6 else f"Produkt aus {len(sets)} Faktoren"
    res.title = f"Erzeugende Funktion: Koeffizient von {_pow(t)}"
    res.summary = f"{_fmt(res.count)} Lösungen für die Summe {t}."
    res.steps.append(Step("Gleichung", f"x₁ + … + x{str(len(sets)).translate(str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉'))} = {t}, jedes xᵢ nur aus seiner Menge. "
                          "Addieren der Variablen wird als Multiplizieren der Potenzen simuliert: x^a · x^b = x^(a+b).",
                          items=[(f"x{i + 1}", "{" + ", ".join(map(str, f)) + "}") for i, f in enumerate(sets)] if len(sets) <= 10 else [],
                          rule="erzeugende Funktion"))
    res.steps.append(Step("Erzeugende Funktion", "Ein Faktor je Variable: jede erlaubte Zahl als Exponent.", items=[("f(x)", res.formula)], rule="erzeugende Funktion"))
    res.steps.append(Step("Ausmultiplizieren", "Alle Produkte ausmultiplizieren und gleiche Potenzen zusammenfassen.", table=_poly_table(poly, t), rule="erzeugende Funktion"))
    res.steps.append(Step("Koeffizient ablesen", f"Der Koeffizient von {_pow(t)} ist die Anzahl der Lösungen.", items=[(f"[{_pow(t)}]", _fmt(res.count))], rule="erzeugende Funktion"))
    total = math.prod(len(f) for f in sets)
    if total <= MAX_BRUTE:
        got = sum(1 for c in itertools.product(*sets) if sum(c) == t)
        if got != res.count:
            raise AssertionError("Aufzählung weicht vom Koeffizienten ab")          # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Alle {_fmt(total)} Kombinationen durchgegangen: {_fmt(got)} mit Summe {t}."))
    return res._finish()


def gf_coins(coins, target: int, ordered: bool = False) -> GFResult:
    """
    Wie viele Möglichkeiten gibt es, den Betrag ``target`` mit Münzen ``coins`` zu bezahlen (Serie 9, Aufgabe 14)?
    ``ordered=False``: nur zählt, wie oft jede Münze vorkommt, Faktor je Münze 1/(1 − xᶜ) = 1 + xᶜ + x²ᶜ + …
    ``ordered=True``: der Reihe nach eingeworfen, 1/(1 − (xᶜ¹ + xᶜ² + …)) = 1 + P + P² + …

    >>> gf_coins([1, 2, 5], 15).count
    18
    >>> gf_coins([1, 2, 5], 15, ordered=True).count
    1843
    """
    cs = sorted(set(_int(c, "Münze", 1, MAX_TARGET) for c in coins))
    if not cs:
        raise ValueError("Es braucht mindestens eine Münze")
    t = _int(target, "Betrag", 0, MAX_TARGET)
    res = GFResult()
    res.target = t
    cs_txt = ", ".join(map(str, cs))
    if not ordered:
        poly: dict = {0: 1}
        for c in cs:
            poly = _mul(poly, {c * j: 1 for j in range(t // c + 1)}, cap=t)
        res.formula = " · ".join(f"1/(1 − {_pow(c)})" for c in cs)
        res.title = f"Betrag {t} mit Münzen {cs_txt} bezahlen (ohne Reihenfolge)"
        res.steps.append(Step("Modellieren", "Anzahl a_c der Münzen je Wert c mit " + " + ".join(f"{c}·a{c}" for c in cs) + f" = {t}. "
                              "Eine Münze vom Wert c trägt 0, c, 2c, … bei: Faktor 1 + xᶜ + x²ᶜ + … = 1/(1 − xᶜ).", rule="erzeugende Funktion"))
        res.steps.append(Step("Erzeugende Funktion", "Ein Faktor je Münzwert (bis zum Betrag abgeschnitten).",
                              items=[("f(x)", res.formula)], rule="erzeugende Funktion"))
    else:
        base = {c: 1 for c in cs}
        poly = {0: 1}
        power = {0: 1}
        for _ in range(t):
            power = _mul(power, base, cap=t)
            if not power:
                break
            for k, v in power.items():
                poly[k] = poly.get(k, 0) + v
        res.formula = f"1/(1 − ({_poly(cs)}))"
        res.title = f"Betrag {t} mit Münzen {cs_txt} der Reihe nach einwerfen"
        res.steps.append(Step("Modellieren", f"Eine Folge von k Münzen hat die Summe {t}. Ein Einwurf trägt " + ", ".join(map(str, cs)) + " bei, "
                              f"das ist P = {_poly(cs)}; k Einwürfe Pᵏ (jede Reihenfolge ein eigener Term). Alle Längen: 1 + P + P² + … = 1/(1 − P).",
                              rule="erzeugende Funktion"))
        res.steps.append(Step("Erzeugende Funktion", "Summe über alle Längen k, bis zum Betrag abgeschnitten.", items=[("f(x)", res.formula)], rule="erzeugende Funktion"))
    res.poly = poly
    res.count = poly.get(t, 0)
    res.summary = f"{_fmt(res.count)} Möglichkeiten für {t}."
    res.steps.append(Step("Ausmultiplizieren", "Koeffizienten der Potenzreihe bis zum Betrag.", table=_poly_table(poly, t), rule="erzeugende Funktion"))
    res.steps.append(Step("Koeffizient ablesen", f"Der Koeffizient von {_pow(t)} ist die Anzahl.", items=[(f"[{_pow(t)}]", _fmt(res.count))], rule="erzeugende Funktion"))
    # Probe durch Aufzählen ohne Potenzreihe
    if not ordered:
        def enum(i, rest):
            if i == len(cs):
                return 1 if rest == 0 else 0
            return sum(enum(i + 1, rest - cs[i] * j) for j in range(rest // cs[i] + 1))
        got = enum(0, t) if t <= 400 else None
    else:
        def seqs(rest):
            if rest == 0:
                return 1
            return sum(seqs(rest - c) for c in cs if c <= rest)
        got = seqs(t) if t <= 20 else None
    if got is not None:
        if got != res.count:
            raise AssertionError("Aufzählung weicht vom Koeffizienten ab")          # nie erwartet
        res.checked = True
        res.steps.append(Step("Probe", f"Ohne Potenzreihe direkt aufgezählt: {_fmt(got)}, stimmt."))
    return res._finish()
