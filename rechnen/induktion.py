#!/usr/bin/env python3
"""
Mathematische Induktion (Semesterwoche 7, Serie 7).

Was hier steht (alles exakt gerechnet, nie ``eval``/``exec`` auf Eingaben):

    prove_sum(term, closed, ...)        Summenformel mit schwacher Induktion beweisen (Aufgaben 1 bis 4)
    prove_residue(base, mod, allowed)   baseⁿ mod m liegt immer in einer Menge: while-Schleife terminiert nie
                                        (Aufgaben 6 und 7)
    prove_divisible(a, b, m)            m teilt aⁿ − bⁿ für alle n: while-Schleife terminiert nie (Aufgabe 5)
    tile_board(n, hole)                 Parkettierung mit Winkel-Fliesen, rekursiv wie der Induktionsbeweis (Aufgabe 8)
    knight_walk(n)                      Springerweg über alle Felder (Aufgabe 9, optional)
    coins(n)                            Zwei- und Fünffränkler für n >= 4 Franken, starke Induktion (Aufgabe 10)
    quick_sort(A, ...)                  quickSort mit Rekursionsbaum, Korrektheit mit starker Induktion (Aufgabe 11)
    INDUCTION_CODE                      der Code der Serie als Text

Aufbau eines Induktionsbeweises (Serie 7, Frage 1 und 2):

  * Induktionsverankerung: P(n₀) ist wahr.
  * Induktionsschritt schwach: aus P(n) folgt P(n+1), für alle n ≥ n₀.
  * Induktionsschritt stark: aus P(n₀) ∧ … ∧ P(n) folgt P(n+1).

Hinweise zu den Unterlagen (auch im Abschlussbericht vermerkt):
  * Die PDF-Serie enthält nur die Aufgabenstellungen, keine Lösungen. Die Beweise hier sind eigene Rechnungen;
    jede Aussage wird zusätzlich an konkreten Werten nachgerechnet (Probe).
  * Aufgabe 4 nennt den Algorithmus ``summe(s, n, q)``, gemeint ist die Summe der ersten n ungeraden Zahlen,
    also ``return n**2`` (Schreibfehler in der Serie, die Parameter s und q kommen nicht vor).
  * Aufgabe 9: Das Modul liefert den Weg (und prüft ihn), den Induktionsbeweis selbst nicht.
    TODO: Induktionsbeweis zu Aufgabe 9 (Rand um ein Brett legen) mit der Vorlesung abgleichen.
"""

from __future__ import annotations

import ast
import random
import textwrap
from collections import deque
from fractions import Fraction

import sympy as sp

from .render import Result, Step, Table
from .rekursion import RecNode

# ==========================================================================
# Grenzen
# ==========================================================================

MAX_PROBE = 10                 # Probe bis n₀ + 10
MAX_TILING_N = 5               # Brett 2ⁿ × 2ⁿ, höchstens 32 × 32
MAX_KNIGHT_N = 12
MAX_COINS_N = 10 ** 6
MAX_LIST_LEN = 32              # quickSort-Baum
MAX_RESIDUE = 10 ** 6

__all__ = ["InductionResult", "prove_sum", "prove_residue", "prove_divisible", "TilingResult", "tile_board",
           "KnightResult", "knight_walk", "CoinsResult", "coins", "QuickSortResult", "quick_sort",
           "INDUCTION_CODE"]

# ==========================================================================
# Code der Serie
# ==========================================================================

INDUCTION_CODE = {
    "summe_arith": textwrap.dedent("""\
        def summe(s, n, d):
            return n*s + n*(n-1)/2*d"""),
    "summe_geom": textwrap.dedent("""\
        def summe(s, n, q):
            return s*(q**n - 1)/(q - 1)"""),
    "summQuad": textwrap.dedent("""\
        def summQuad(n):
            return n*(n+1)*(2*n+1)/6"""),
    "summe_ungerade": textwrap.dedent("""\
        def summe(s, n, q):      # so steht es in der Serie; gemeint ist die Summe der ersten n ungeraden Zahlen
            return n**2"""),
    "schleife_5": textwrap.dedent("""\
        n = 0
        while (8**n - 3**n) % 5 == 0:
            print('Hallo Welt!')
            n = n + 1"""),
    "schleife_6": textwrap.dedent("""\
        n = 0
        while 9**n % 10 == 1 or 9**n % 10 == 9:
            print('Hallo Welt!')
            n = n + 1"""),
    "schleife_7": textwrap.dedent("""\
        n = 0
        while 2**n % 7 == 1 or 2**n % 7 == 2 or 2**n % 7 == 4:
            print('Hallo Welt!')
            n = n + 1"""),
    # genau der Text aus Serie 7 (das »ielse« im PDF ist ein Satzfehler für »else«)
    "quickSort": textwrap.dedent("""\
        import random as rd
        def quickSort(A):
            if len(A) <= 1:
                return A
            pivot = rd.randint(0, len(A)-1)
            L = []
            R = []
            for i in range(len(A)):
                if i != pivot:
                    if A[i] < A[pivot]:
                        L.append(A[i])
                    else:
                        R.append(A[i])
            L = quickSort(L)
            R = quickSort(R)
            return L + [A[pivot]] + R"""),
}


# ==========================================================================
# Sicherer Term-Parser (mehrere Variablen)
# ==========================================================================

_NAME_MAX = 4


def _parse(text, extra: dict | None = None) -> sp.Expr:
    """Term mit Zahlen, Namen, + − * / ** und Klammern lesen — ohne ``eval`` (nur AST-Positivliste)."""
    if isinstance(text, sp.Basic):
        return text
    if isinstance(text, bool) or not isinstance(text, (str, int)):
        raise ValueError("Ein Term muss ein Text wie 'n*(n+1)/2' sein")
    if isinstance(text, int):
        return sp.Integer(text)
    s = text.strip().replace("^", "**").replace("·", "*").replace("−", "-").replace("×", "*")
    if not s or len(s) > 200:
        raise ValueError("Term leer oder länger als 200 Zeichen")
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError:
        raise ValueError(f"Der Term '{text}' kann nicht gelesen werden") from None
    extra = extra or {}

    def conv(node, depth=0):
        if depth > 40:
            raise ValueError("Term zu tief verschachtelt")
        if isinstance(node, ast.Expression):
            return conv(node.body, depth + 1)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, int) or node.value.bit_length() > 100:
                raise ValueError("Nur ganze Zahlen sind als Konstanten erlaubt")
            return sp.Integer(node.value)
        if isinstance(node, ast.Name):
            if not (node.id.isidentifier() and len(node.id) <= _NAME_MAX):
                raise ValueError(f"Name '{node.id}' ist zu lang (höchstens {_NAME_MAX} Zeichen)")
            return extra.get(node.id) or sp.Symbol(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = conv(node.operand, depth + 1)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp):
            a, b = conv(node.left, depth + 1), conv(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                if b == 0:
                    raise ValueError("Division durch 0")
                return a / b
            if isinstance(node.op, ast.Pow):
                if b.is_Number and abs(b) > 1000:
                    raise ValueError("Exponent zu gross")
                return a ** b
        raise ValueError("Erlaubt sind nur Zahlen, Namen, + - * / ** und Klammern")
    return conv(tree)


def _int(v, name, lo, hi) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name} muss eine ganze Zahl sein, nicht {v!r}")
    if not lo <= v <= hi:
        raise ValueError(f"{name} muss zwischen {lo} und {hi} liegen")
    return v


# ==========================================================================
# Schwache Induktion: Summenformeln (Aufgaben 1 bis 4)
# ==========================================================================

class InductionResult(Result):
    """
    ``valid`` (Verankerung und Schritt gelungen), ``anchor_ok``, ``step_ok``, ``n0``,
    ``difference`` (P(n+1) minus IH-Einsetzung, 0 wenn der Schritt aufgeht), ``counterexample`` (kleinstes n der Probe,
    das nicht stimmt, oder None), ``rows`` (Probe als Liste von (n, linke Seite, rechte Seite)).
    """


def _sum_text(term, first, last, var="i"):
    return f"Σ({var}={sp.sstr(first)}…{sp.sstr(last)}) [{sp.sstr(term)}]"


def prove_sum(term, closed, *, first=1, last="n", n0=1, var: str = "n", index: str = "i",
              params: dict | None = None, name: str = "S") -> InductionResult:
    """
    Beweist mit schwacher Induktion: Σ_{i=first}^{last(n)} term(i) = closed(n) für alle n ≥ n₀ (Serie 7, Aufgaben 1 bis 4).

    ``term`` ist der Summand in ``index``, ``closed`` der Term des Algorithmus in ``var`` (Python-Schreibweise,
    ``^`` oder ``**``). ``last`` ist die obere Grenze (``"n"`` oder ``"n-1"``). Weitere Namen (s, d, q) sind
    frei wählbare Zahlen; die Probe rechnet mit ``params`` (Standard: 3, 2, 5, 7 der Reihe nach).

    >>> prove_sum("2*i-1", "n**2").valid
    True
    >>> prove_sum("i", "n*(n+1)/2 + 1").valid
    False
    """
    n, i = sp.Symbol(var, integer=True, positive=True), sp.Symbol(index, integer=True)
    n0 = _int(n0, "n0", 0, 1000)
    T = _parse(term, {index: i, var: n})
    C = _parse(closed, {var: n, index: i})
    first_e = _parse(first, {var: n})
    last_e = _parse(last, {var: n})
    if not last_e.has(n) or sp.simplify(last_e.subs(n, n + 1) - last_e) != 1:
        raise ValueError("Die obere Grenze muss mit n um genau 1 wachsen, etwa 'n' oder 'n-1'")
    if first_e.has(n) or first_e.has(i):
        raise ValueError("Die untere Grenze muss eine feste Zahl sein")
    if C.has(i):
        raise ValueError(f"closed darf nur {var} und die Parameter enthalten, nicht {index}")
    others = sorted((T.free_symbols | C.free_symbols) - {n, i}, key=str)
    defaults = [3, 2, 5, 7, 11, 13]
    vals = {s: sp.nsimplify((params or {}).get(str(s), defaults[k % len(defaults)])) for k, s in enumerate(others)}
    for s, v in vals.items():
        if v.free_symbols or not v.is_real:
            raise ValueError(f"Wert für {s} muss eine Zahl sein")

    res = InductionResult()
    res.n0 = n0
    S = f"{name}({var})"
    claim = f"{_sum_text(T, first_e, last_e, index)} = {sp.sstr(C)}"
    res.title = f"Schwache Induktion: {claim}"
    res.summary = f"Behauptung P({var}): {claim}, für alle {var} ≥ {n0}."
    # -- Verankerung ------------------------------------------------------
    upper0 = int(last_e.subs(n, n0))
    left0 = sum((T.subs(i, k) for k in range(int(first_e), upper0 + 1)), sp.Integer(0))
    right0 = C.subs(n, n0)
    res.anchor_ok = sp.simplify(left0 - right0) == 0
    shown = " + ".join(sp.sstr(T.subs(i, k)) for k in range(int(first_e), upper0 + 1)) or "0 (leere Summe)"
    res.steps.append(Step(
        f"Induktionsverankerung P({n0})", f"Links: {shown} = {sp.sstr(sp.simplify(left0))}. "
        f"Rechts: {sp.sstr(C)} mit {var} = {n0} ergibt {sp.sstr(sp.simplify(right0))}. "
        + ("Beide Seiten sind gleich, also ist P(" + str(n0) + ") wahr." if res.anchor_ok else "Die Seiten sind verschieden: P(" + str(n0) + ") ist falsch."),
        items=[("links", sp.simplify(left0)), ("rechts", sp.simplify(right0))], rule="Induktionsverankerung"))
    # -- Schritt ----------------------------------------------------------
    nxt = last_e.subs(n, n + 1)
    new_term = T.subs(i, nxt)
    res.steps.append(Step(
        "Induktionsvoraussetzung", f"Für ein festes {var} ≥ {n0} gelte P({var}): {S} = {sp.sstr(C)}.",
        rule="Induktionsvoraussetzung"))
    res.steps.append(Step(
        f"Induktionsschritt: P({var}) ⇒ P({var}+1)",
        f"Die Summe bis {sp.sstr(nxt)} ist die Summe bis {sp.sstr(last_e)} plus der neue Summand "
        f"{sp.sstr(T)} mit {index} = {sp.sstr(nxt)}. Die Induktionsvoraussetzung ersetzt die alte Summe:",
        items=[(f"{name}({var}+1)", f"{sp.sstr(C)} + ({sp.sstr(new_term)})"),
               (f"Behauptung P({var}+1)", C.subs(n, n + 1))], rule="Induktionsschritt"))
    diff = sp.simplify(sp.expand(sp.together(C + new_term - C.subs(n, n + 1))))
    if diff != 0:
        diff = sp.simplify(sp.powsimp(sp.expand_power_exp(sp.expand(sp.together(C + new_term - C.subs(n, n + 1))))))
    res.difference = diff
    res.step_ok = diff == 0
    res.steps.append(Step(
        "Umformen", ("Die Differenz aus (IH eingesetzt) und der Behauptung P(n+1) ist 0: beide Seiten sind gleich."
                     if res.step_ok else "Die Differenz aus (IH eingesetzt) und der Behauptung P(n+1) ist nicht 0: der Schritt geht nicht auf."),
        items=[("Differenz", diff)], rule="Termumformung"))
    for d in sorted({sp.denom(sp.together(C))} - {1}, key=str):
        if d.free_symbols - {n}:
            res.steps[-1].note = (f"Voraussetzung: {sp.sstr(d)} ≠ 0 (sonst teilt der Algorithmus durch 0)."
                                  if not res.steps[-1].note else res.steps[-1].note)
            res.warnings.append(f"Der Algorithmus teilt durch {sp.sstr(d)}: nur für {sp.sstr(d)} ≠ 0 definiert.")
    # -- Probe an konkreten Werten ----------------------------------------
    rows, bad = [], None
    for m in range(n0, n0 + MAX_PROBE + 1):
        up = int(last_e.subs(n, m))
        lhs = sum((T.subs(vals).subs(i, k) for k in range(int(first_e), up + 1)), sp.Integer(0))
        rhs = C.subs(vals).subs(n, m)
        rows.append((m, sp.nsimplify(lhs), sp.nsimplify(rhs)))
        if bad is None and sp.simplify(lhs - rhs) != 0:
            bad = m
    res.rows, res.counterexample = rows, bad
    pv = ", ".join(f"{s} = {sp.sstr(v)}" for s, v in vals.items())
    res.steps.append(Step(
        "Probe", ("Mit " + pv + ": " if pv else "") + "Summe ausgerechnet und Formel ausgewertet.",
        table=Table([var, "Summe", "Formel"], [[str(m), sp.sstr(a), sp.sstr(b)] for m, a, b in rows],
                    marks={k: ("ok" if a == b else "bad") for k, (m, a, b) in enumerate(rows)})))
    res.valid = bool(res.anchor_ok and res.step_ok)
    if res.valid:
        res.steps.append(Step(
            "Schluss", f"P({n0}) gilt, und aus P({var}) folgt P({var}+1). Also gilt P({var}) für alle {var} ≥ {n0}: "
            "der Algorithmus ist korrekt.", rule="Prinzip der schwachen Induktion"))
    else:
        res.steps.append(Step(
            "Schluss", "Der Beweis gelingt nicht" + (f"; Gegenbeispiel schon bei {var} = {bad}" if bad is not None else "")
            + ". Das heisst nur: dieser Weg beweist nichts. Die Probe zeigt, ob die Behauptung wirklich falsch ist.",
            rule="Prinzip der schwachen Induktion"))
    res.highlights = [("Behauptung", "bewiesen" if res.valid else "nicht bewiesen")]
    return res


# ==========================================================================
# Schwache Induktion: while-Schleifen, die nie enden (Aufgaben 5 bis 7)
# ==========================================================================

def prove_residue(base: int, mod: int, allowed, *, n0: int = 0) -> InductionResult:
    """
    P(n): baseⁿ mod m ∈ ``allowed`` gilt für alle n ≥ n₀ — damit terminiert
    ``while base**n % m in allowed`` nie (Serie 7, Aufgaben 6 und 7).

    Verankerung: baseⁿ⁰ mod m ∈ allowed. Schritt: baseⁿ⁺¹ = base · baseⁿ, also
    ``base·r mod m`` für jeden erlaubten Rest r wieder in ``allowed``.

    >>> prove_residue(9, 10, [1, 9]).valid
    True
    >>> prove_residue(2, 7, [1, 2, 4]).valid
    True
    >>> prove_residue(2, 7, [1, 2]).valid
    False
    """
    base, mod = _int(base, "base", 2, MAX_RESIDUE), _int(mod, "mod", 2, MAX_RESIDUE)
    n0 = _int(n0, "n0", 0, 1000)
    try:
        allowed = sorted({_int(r, "Rest", 0, mod - 1) for r in allowed})
    except TypeError:
        raise ValueError("allowed: eine Liste von Resten, etwa [1, 9]") from None
    if not allowed:
        raise ValueError("allowed darf nicht leer sein")
    res = InductionResult()
    res.n0 = n0
    cond = " ∨ ".join(f"{base}ⁿ mod {mod} = {r}" for r in allowed)
    res.title = f"Schwache Induktion: {base}ⁿ mod {mod} ∈ {{{', '.join(map(str, allowed))}}}"
    res.summary = (f"P(n): {cond}. Gilt P(n) für alle n ≥ {n0}, ist die Schleifenbedingung immer wahr "
                   "und die while-Schleife terminiert nicht.")
    r0 = pow(base, n0, mod)
    res.anchor_ok = r0 in allowed
    res.steps.append(Step(
        f"Induktionsverankerung P({n0})", f"{base}^{n0} = {base ** n0}, Rest bei Division durch {mod}: {r0}. "
        + (f"{r0} liegt in der Menge, P({n0}) ist wahr." if res.anchor_ok else f"{r0} liegt nicht in der Menge: P({n0}) ist falsch."),
        items=[(f"{base}^{n0} mod {mod}", r0)], rule="Induktionsverankerung"))
    res.steps.append(Step("Induktionsvoraussetzung", f"Für ein festes n ≥ {n0} gelte P(n): {base}ⁿ mod {mod} ∈ {{{', '.join(map(str, allowed))}}}.",
                          rule="Induktionsvoraussetzung"))
    rows, marks, step_ok = [], {}, True
    for k, r in enumerate(allowed):
        nr = base * r % mod
        good = nr in allowed
        step_ok = step_ok and good
        marks[k] = "ok" if good else "bad"
        rows.append([f"{base}ⁿ mod {mod} = {r}", f"{base}ⁿ⁺¹ = {base}·{base}ⁿ", f"{base}·{r} = {base * r}  ->  Rest {nr}", "ja" if good else "nein"])
    res.step_ok = step_ok
    res.steps.append(Step(
        "Induktionsschritt: P(n) ⇒ P(n+1)", f"Es ist {base}ⁿ⁺¹ = {base}·{base}ⁿ. Der Rest von {base}ⁿ⁺¹ hängt nur vom Rest von {base}ⁿ ab "
        "(Rechnen mit Resten), also genügt jeder erlaubte Rest einzeln.",
        table=Table(["Rest von aⁿ", "Umformung", "Rechnung", f"wieder in der Menge?"], rows, marks=marks),
        rule="Induktionsschritt"))
    seq = [pow(base, m, mod) for m in range(n0, n0 + MAX_PROBE + 1)]
    bad = next((n0 + k for k, r in enumerate(seq) if r not in allowed), None)
    res.counterexample = bad
    res.rows = [(n0 + k, r) for k, r in enumerate(seq)]
    res.steps.append(Step("Probe", f"Die ersten Reste von {base}ⁿ mod {mod}, direkt ausgerechnet.",
                          table=Table(["n"] + [str(n0 + k) for k in range(len(seq))], [[f"{base}ⁿ mod {mod}"] + [str(r) for r in seq]],
                                      )))
    res.valid = bool(res.anchor_ok and res.step_ok)
    if res.valid:
        res.steps.append(Step("Schluss", f"P({n0}) gilt, und aus P(n) folgt P(n+1). Also gilt P(n) für alle n ≥ {n0}: "
                              "die Bedingung bleibt immer wahr, die while-Schleife terminiert nie.", rule="Prinzip der schwachen Induktion"))
    else:
        res.steps.append(Step("Schluss", "Der Beweis gelingt nicht" + (f"; die Bedingung ist bei n = {bad} schon falsch, die Schleife endet dort" if bad is not None else "")
                              + ".", rule="Prinzip der schwachen Induktion"))
    res.highlights = [("Schleife terminiert nie", res.valid)]
    return res


def prove_divisible(a: int, b: int, m: int, *, n0: int = 0) -> InductionResult:
    """
    P(n): m teilt aⁿ − bⁿ, für alle n ≥ n₀ — damit terminiert ``while (a**n - b**n) % m == 0`` nie
    (Serie 7, Aufgabe 5, a = 8, b = 3, m = 5).

    Schritt: aⁿ⁺¹ − bⁿ⁺¹ = a·(aⁿ − bⁿ) + (a − b)·bⁿ. Der erste Summand ist durch die Induktionsvoraussetzung
    durch m teilbar, der zweite, wenn m die Zahl a − b teilt.

    >>> prove_divisible(8, 3, 5).valid
    True
    >>> prove_divisible(8, 3, 7).valid
    False
    """
    a, b, m = _int(a, "a", 1, MAX_RESIDUE), _int(b, "b", 1, MAX_RESIDUE), _int(m, "m", 2, MAX_RESIDUE)
    n0 = _int(n0, "n0", 0, 1000)
    res = InductionResult()
    res.n0 = n0
    res.title = f"Schwache Induktion: {m} teilt {a}ⁿ − {b}ⁿ"
    res.summary = f"P(n): ({a}ⁿ − {b}ⁿ) mod {m} = 0. Gilt P(n) für alle n ≥ {n0}, terminiert die while-Schleife nicht."
    v0 = a ** n0 - b ** n0
    res.anchor_ok = v0 % m == 0
    res.steps.append(Step(f"Induktionsverankerung P({n0})", f"{a}^{n0} − {b}^{n0} = {v0}, und {v0} mod {m} = {v0 % m}. "
                          + (f"{m} teilt {v0}: P({n0}) ist wahr." if res.anchor_ok else f"{m} teilt {v0} nicht: P({n0}) ist falsch."),
                          items=[("Wert", v0)], rule="Induktionsverankerung"))
    res.steps.append(Step("Induktionsvoraussetzung", f"Für ein festes n ≥ {n0} gelte P(n): {m} teilt {a}ⁿ − {b}ⁿ, also {a}ⁿ − {b}ⁿ = {m}·k mit k ganz.",
                          rule="Induktionsvoraussetzung"))
    res.step_ok = (a - b) % m == 0
    res.steps.append(Step(
        "Induktionsschritt: P(n) ⇒ P(n+1)",
        f"{a}ⁿ⁺¹ − {b}ⁿ⁺¹ = {a}·({a}ⁿ − {b}ⁿ) + ({a} − {b})·{b}ⁿ = {a}·{m}·k + {a - b}·{b}ⁿ. "
        f"Der erste Summand ist durch {m} teilbar (Induktionsvoraussetzung). "
        + (f"Der zweite auch, denn {m} teilt {a} − {b} = {a - b}. Also teilt {m} die ganze Summe." if res.step_ok
           else f"Der zweite nicht sicher: {m} teilt {a} − {b} = {a - b} nicht. Der Schritt gelingt so nicht."),
        rule="Induktionsschritt"))
    seq = [(a ** k - b ** k) % m for k in range(n0, n0 + MAX_PROBE + 1)]
    res.counterexample = next((n0 + k for k, r in enumerate(seq) if r != 0), None)
    res.rows = [(n0 + k, r) for k, r in enumerate(seq)]
    res.steps.append(Step("Probe", f"({a}ⁿ − {b}ⁿ) mod {m}, direkt ausgerechnet.",
                          table=Table(["n"] + [str(n0 + k) for k in range(len(seq))], [["Rest"] + [str(r) for r in seq]])))
    res.valid = bool(res.anchor_ok and res.step_ok)
    res.steps.append(Step("Schluss", (f"P({n0}) gilt, und aus P(n) folgt P(n+1). Also gilt P(n) für alle n ≥ {n0}: "
                                      "die Bedingung bleibt immer wahr, die while-Schleife terminiert nie.") if res.valid
                          else "Der Beweis gelingt nicht" + (f"; die Bedingung ist bei n = {res.counterexample} schon falsch" if res.counterexample is not None else "") + ".",
                          rule="Prinzip der schwachen Induktion"))
    res.highlights = [("Schleife terminiert nie", res.valid)]
    return res


# ==========================================================================
# Aufgabe 8: Parkettierung mit Winkel-Fliesen
# ==========================================================================

class TilingResult(Result):
    """``grid`` (Zeilen von oben nach unten, Fliesen-Nummer je Feld, 0 beim freien Feld), ``hole`` (Zeile, Spalte),
    ``tiles`` (Anzahl Fliesen = (4ⁿ − 1)/3), ``size`` (2ⁿ), ``n``."""

    def figure(self, *, dark: bool = False, figsize=None, title=None):
        from ..grafik.plots import plot_tiling
        return plot_tiling(self.grid, self.hole, dark=dark, figsize=figsize, title=title)


def _tile(grid, top, left, size, hole, counter):
    """Füllt das Quadrat (top, left, size) rekursiv; ``hole`` = (Zeile, Spalte) bleibt frei."""
    if size == 1:
        return
    half = size // 2
    mid_r, mid_c = top + half, left + half
    counter[0] += 1
    t = counter[0]
    quads = [(top, left), (top, mid_c), (mid_r, left), (mid_r, mid_c)]          # oben links, oben rechts, unten links, unten rechts
    corners = [(mid_r - 1, mid_c - 1), (mid_r - 1, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c)]   # Eckfeld zur Mitte hin
    for (qr, qc), corner in zip(quads, corners):
        if qr <= hole[0] < qr + half and qc <= hole[1] < qc + half:
            sub_hole = hole
        else:
            grid[corner[0]][corner[1]] = t                                       # die eine Fliese deckt dieses Eckfeld
            sub_hole = corner
        _tile(grid, qr, qc, half, sub_hole, counter)


def tile_board(n: int, hole=(0, 0)) -> TilingResult:
    """
    Parkettierung eines Schachbretts mit 2ⁿ × 2ⁿ Feldern durch Winkel-Fliesen (drei Quadrate, keine Linie).
    Alles ausser einem Feld ``hole`` = (Zeile, Spalte), von 0 an, wird genau einmal überdeckt (Serie 7, Aufgabe 8).

    Das Verfahren ist der Induktionsbeweis selbst: Brett in vier Quadrate teilen, eine Fliese in die Mitte legen,
    so dass jedes Quadrat ein einzelnes freies Feld hat, dann viermal dasselbe mit n − 1.

    >>> r = tile_board(2, (1, 2)); r.tiles
    5
    """
    n = _int(n, "n", 1, MAX_TILING_N)
    size = 2 ** n
    if (not isinstance(hole, (tuple, list)) or len(hole) != 2 or not all(isinstance(x, int) and not isinstance(x, bool) for x in hole)
            or not (0 <= hole[0] < size and 0 <= hole[1] < size)):
        raise ValueError(f"hole: ein Feld (Zeile, Spalte) mit Werten von 0 bis {size - 1}")
    hole = (hole[0], hole[1])
    grid = [[0] * size for _ in range(size)]
    counter = [0]
    _tile(grid, 0, 0, size, hole, counter)
    # Prüfung: jedes Feld ausser hole genau einmal, jede Fliese ein Winkel
    cells: dict[int, list] = {}
    for r in range(size):
        for c in range(size):
            if (r, c) == hole:
                if grid[r][c] != 0:
                    raise AssertionError("freies Feld belegt")                    # nie erwartet
            else:
                cells.setdefault(grid[r][c], []).append((r, c))
    if 0 in cells or len(cells) != (4 ** n - 1) // 3 or any(len(v) != 3 for v in cells.values()):
        raise AssertionError("Parkettierung unvollständig")                        # nie erwartet
    for v in cells.values():
        rs, cs = {p[0] for p in v}, {p[1] for p in v}
        if len(rs) != 2 or len(cs) != 2:                                           # drei Felder eines 2×2-Blocks
            raise AssertionError("Fliese ist kein Winkel")                         # nie erwartet
    res = TilingResult()
    res.n, res.size, res.grid, res.hole, res.tiles = n, size, grid, hole, counter[0]
    res.title = f"Parkettierung mit Winkel-Fliesen: {size} × {size}, freies Feld {hole}"
    res.summary = f"{res.tiles} = (4^{n} − 1)/3 Fliesen decken alle {size * size - 1} Felder ausser {hole} genau einmal."
    res.steps.append(Step("Behauptung", f"P(n): Ein 2ⁿ × 2ⁿ-Brett lässt sich bis auf ein beliebiges Feld mit Winkel-Fliesen parkettieren, n ≥ 1.",
                          rule="Schwache Induktion"))
    res.steps.append(Step("Induktionsverankerung P(1)", "Ein 2 × 2-Brett hat 4 Felder; bis auf ein beliebiges Feld bleiben 3 Felder, "
                          "die zusammen genau eine Winkel-Fliese bilden.", rule="Induktionsverankerung"))
    res.steps.append(Step("Induktionsschritt P(n) ⇒ P(n+1)",
                          "Das 2ⁿ⁺¹-Brett in vier 2ⁿ-Quadrate teilen. Das freie Feld liegt in genau einem davon. "
                          "In die Mitte kommt eine Winkel-Fliese, die je ein Eckfeld der drei anderen Quadrate deckt. "
                          "Jedes der vier Quadrate hat jetzt genau ein Feld, das nicht zu parkettieren ist; nach Induktionsvoraussetzung "
                          "geht das für alle vier.", rule="Induktionsschritt"))
    res.steps.append(Step("Anzahl Fliesen", f"T(n) = 4·T(n−1) + 1 mit T(1) = 1, also T(n) = (4ⁿ − 1)/3.",
                          items=[(f"T({n})", res.tiles)], rule="Rekursionsbeziehung"))
    if size <= 16:
        res.steps.append(Step("Die Parkettierung", "Gleiche Zahl = gleiche Fliese, ✗ = freies Feld.",
                              table=Table([str(c) for c in range(size)], [["✗" if (r, c) == hole else str(grid[r][c]) for c in range(size)] for r in range(size)])))
    res.highlights = [("Fliesen", res.tiles), ("freie Felder", 1)]
    return res


# ==========================================================================
# Aufgabe 9 (optional): Springerweg
# ==========================================================================

class KnightResult(Result):
    """``path`` (Liste von (Zeile, Spalte), Start (0, 0)), ``length`` (Anzahl Züge), ``revisits`` (Felder, die mehrfach besucht werden), ``n``."""


_KNIGHT = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]


def knight_walk(n: int) -> KnightResult:
    """
    Ein Weg für einen Springer auf einem n × n-Brett, der jedes Feld mindestens einmal besucht (Serie 7, Aufgabe 9, n ≥ 4).

    Vom aktuellen Feld geht es auf kürzestem Weg (Breitensuche) zum nächsten noch nicht besuchten Feld. Das Ergebnis wird
    geprüft: alle Züge sind Springerzüge, alle n² Felder kommen vor. Kein Induktionsbeweis (TODO, siehe Modul).

    >>> knight_walk(4).path[0]
    (0, 0)
    """
    n = _int(n, "n", 4, MAX_KNIGHT_N)

    def nbrs(p):
        for dr, dc in _KNIGHT:
            q = (p[0] + dr, p[1] + dc)
            if 0 <= q[0] < n and 0 <= q[1] < n:
                yield q
    path = [(0, 0)]
    seen = {(0, 0)}
    while len(seen) < n * n:
        prev = {path[-1]: None}
        queue = deque([path[-1]])
        goal = None
        while queue and goal is None:
            cur = queue.popleft()
            for q in nbrs(cur):
                if q not in prev:
                    prev[q] = cur
                    if q not in seen:
                        goal = q
                        break
                    queue.append(q)
        if goal is None:
            raise AssertionError("nicht alle Felder erreichbar")                    # nie erwartet für n >= 4
        leg = []
        while goal is not None and prev[goal] is not None:
            leg.append(goal)
            goal = prev[goal]
        for q in reversed(leg):
            path.append(q)
            seen.add(q)
    for a, b in zip(path, path[1:]):
        if (b[0] - a[0], b[1] - a[1]) not in _KNIGHT:
            raise AssertionError("kein Springerzug")                                # nie erwartet
    res = KnightResult()
    res.n, res.path, res.length = n, path, len(path) - 1
    res.revisits = len(path) - len(seen)
    res.title = f"Springerweg über alle Felder: {n} × {n}"
    res.summary = f"{res.length} Züge, {res.revisits} Felder werden mehrfach besucht (erlaubt: »mindestens einmal«)."
    res.steps.append(Step("Aufgabe", "Ein Weg für einen Springer, der jedes Feld mindestens einmal besucht. Felder dürfen also mehrfach vorkommen.", rule="Behauptung"))
    res.steps.append(Step("Verfahren", "Vom aktuellen Feld auf kürzestem Weg (Breitensuche über Springerzüge) zum nächsten unbesuchten Feld; wiederholen, bis alle n² Felder besucht sind.",
                          rule="Konstruktion"))
    rows = [[str(i), f"({r}, {c})"] for i, (r, c) in enumerate(path)]
    if len(rows) > 40:
        rows = rows[:20] + [["…", "…"]] + rows[-19:]
    res.steps.append(Step("Der Weg", f"{n * n} Felder, alle besucht.", table=Table(["Zug", "Feld (Zeile, Spalte)"], rows),
                          note="TODO: Induktionsbeweis (n → n + 1) der Vorlesung abgleichen; hier wird nur der Weg konstruiert und geprüft."))
    res.highlights = [("Züge", res.length)]
    return res


# ==========================================================================
# Aufgabe 10: Münzen, starke Induktion
# ==========================================================================

class CoinsResult(Result):
    """``a`` (Zweifränkler), ``b`` (Fünffränkler), ``n``, ``chain`` (Betrag, a, b) von n bis zur Verankerung."""


def coins(n: int) -> CoinsResult:
    """
    Zerlegt n ≥ 4 Franken in a Zweifränkler und b Fünffränkler: n = 2a + 5b, a, b ≥ 0 (Serie 7, Aufgabe 10).

    Starke Induktion mit zwei Verankerungen: P(4) mit 2·2, P(5) mit 5. Für n + 1 ≥ 6 gilt P(n − 1) (stark!),
    dazu kommt ein Zweifränkler.

    >>> c = coins(11); (c.a, c.b)
    (3, 1)
    """
    n = _int(n, "n", 4, MAX_COINS_N)
    chain = [n]
    while chain[-1] > 5:
        chain.append(chain[-1] - 2)
    a, b = {4: (2, 0), 5: (0, 1)}[chain[-1]]
    steps_down = len(chain) - 1
    a += steps_down
    if 2 * a + 5 * b != n:
        raise AssertionError("Zerlegung stimmt nicht")                              # nie erwartet
    res = CoinsResult()
    res.n, res.a, res.b = n, a, b
    a0, b0 = {4: (2, 0), 5: (0, 1)}[chain[-1]]
    res.chain = [(m, a0 + (len(chain) - 1 - k), b0) for k, m in enumerate(chain)]
    res.title = f"Münzen: {n} Franken = {a}·2 + {b}·5"
    res.summary = f"{a} Zweifränkler und {b} Fünffränkler ergeben {2 * a + 5 * b} Franken."
    res.steps.append(Step("Behauptung", "P(n): Für n ≥ 4 gibt es a, b ≥ 0 mit n = 2a + 5b.", rule="Starke Induktion"))
    res.steps.append(Step("Induktionsverankerung P(4) und P(5)", "4 = 2·2 + 5·0 und 5 = 2·0 + 5·1. Zwei Verankerungen, weil der Schritt "
                          "zwei zurückgeht.", items=[("P(4)", "a = 2, b = 0"), ("P(5)", "a = 0, b = 1")], rule="Induktionsverankerung"))
    res.steps.append(Step("Induktionsschritt (stark)", "Sei n + 1 ≥ 6. Dann ist n − 1 ≥ 4 und kleiner als n + 1, P(n − 1) darf benutzt werden: "
                          "n − 1 = 2a + 5b. Also n + 1 = 2(a + 1) + 5b.", rule="Starke Induktion",
                          note="Bei schwacher Induktion stünde nur P(n) zur Verfügung, aber n + 1 ergibt sich aus n − 1, nicht aus n."))
    rows = [[str(m), "Verankerung" if k == len(chain) - 1 else f"{m} = ({m} − 2) + 2", str(x), str(y)] for k, (m, x, y) in enumerate(res.chain)]
    if len(rows) > 12:
        rows = rows[:6] + [["…"] * 4] + rows[-5:]
    res.steps.append(Step("Von n bis zur Verankerung", f"{steps_down} Mal zwei Franken abziehen.",
                          table=Table(["Betrag", "Herkunft", "a", "b"], rows)))
    res.highlights = [("a (Zweifränkler)", a), ("b (Fünffränkler)", b)]
    return res


# ==========================================================================
# Aufgabe 11: quickSort, starke Induktion
# ==========================================================================

class QuickSortResult(Result):
    """``value`` (sortierte Liste), ``root`` (``RecNode``-Baum), ``nodes``, ``calls``, ``pivots`` (Pivot je Aufruf)."""

    def figure(self, *, values: bool = False, dark: bool = False, figsize=None, title=None):
        from ..grafik.plots import plot_recursion_tree
        return plot_recursion_tree(self.root, values=values, dark=dark, figsize=figsize, title=title)


def quick_sort(A, *, pivot: str = "random", seed=None) -> QuickSortResult:
    """
    quickSort der Serie 7 (Aufgabe 11) mit Rekursionsbaum; Pivot ist ein Index (``"random"`` wie ``rd.randint(0, len(A)-1)``,
    ``"first"``, ``"middle"`` oder ``"last"``). Kleinere Elemente kommen nach L, alle anderen (auch gleiche) nach R.

    Geprüft wird, was der Beweis mit starker Induktion zeigt: das Ergebnis ist eine sortierte Permutation der Eingabe.

    >>> quick_sort([4, 6, 5, 1, 7, 4, 3, 1], pivot="first").value
    [1, 1, 3, 4, 4, 5, 6, 7]
    """
    if not isinstance(A, (list, tuple)) or not all(isinstance(x, int) and not isinstance(x, bool) for x in A):
        raise ValueError("A muss eine Liste ganzer Zahlen sein")
    if not 1 <= len(A) <= MAX_LIST_LEN:
        raise ValueError(f"A muss 1 bis {MAX_LIST_LEN} Elemente haben")
    if pivot not in ("random", "first", "middle", "last"):
        raise ValueError("pivot: 'random', 'first', 'middle' oder 'last'")
    rng = random.Random(seed)
    pivots: list[int] = []

    def choose(m: int) -> int:
        return {"random": lambda: rng.randint(0, m - 1), "first": lambda: 0, "middle": lambda: m // 2, "last": lambda: m - 1}[pivot]()

    def build(lst: list, depth: int) -> RecNode:
        node = RecNode(str(lst), depth=depth)
        if len(lst) <= 1:
            node.value = list(lst)
            return node
        p = choose(len(lst))
        pivots.append(lst[p])
        L = [x for i, x in enumerate(lst) if i != p and x < lst[p]]
        R = [x for i, x in enumerate(lst) if i != p and not x < lst[p]]
        node.children = [build(L, depth + 1), build(R, depth + 1)]
        node.value = node.children[0].value + [lst[p]] + node.children[1].value
        node.pivot, node.L, node.R = lst[p], L, R
        return node
    root = build(list(A), 0)
    if root.value != sorted(A):
        raise AssertionError("quickSort liefert keine sortierte Permutation")      # nie erwartet
    res = QuickSortResult()
    res.root, res.value, res.nodes = root, root.value, list(root.walk())
    res.calls, res.pivots = len(res.nodes), pivots
    res.title = f"quickSort: {list(A)}"
    res.summary = f"{res.calls} Aufrufe, Pivot: {pivot}. Ergebnis {root.value}."
    res.steps.append(Step("Behauptung", "P(n): quickSort(A) gibt für jede Liste A der Länge n eine aufsteigend sortierte Liste "
                          "mit denselben Elementen zurück.", rule="Starke Induktion"))
    res.steps.append(Step("Pseudocode", INDUCTION_CODE["quickSort"]))
    res.steps.append(Step("Induktionsverankerung P(0) und P(1)", "Bei len(A) ≤ 1 gibt der Code A zurück: leer oder ein Element ist schon sortiert.",
                          rule="Induktionsverankerung"))
    res.steps.append(Step("Induktionsschritt (stark)",
                          "Sei len(A) = n + 1 ≥ 2. L und R sind kürzer als n + 1 (das Pivot fehlt in beiden), mit |L| + |R| = n. "
                          "Darum gilt P(|L|) und P(|R|) (starke Induktion: alle kleineren Längen). Also sind quickSort(L) und quickSort(R) sortiert. "
                          "Alle Elemente in L sind < Pivot, alle in R sind ≥ Pivot. Daher ist L + [Pivot] + R sortiert, und es "
                          "enthält jedes Element von A genau einmal.", rule="Starke Induktion",
                          note="Schwache Induktion reicht nicht: |L| und |R| sind nicht n, sondern irgendwelche kleineren Längen."))
    rows = [[n.label, str(n.pivot), str(n.L), str(n.R), str(n.value)] for n in res.nodes if n.children]
    if rows:
        res.steps.append(Step("Die Aufrufe", "Nur Aufrufe mit Länge ≥ 2 (die anderen sind der Basisfall).",
                              table=Table(["Aufruf", "Pivot", "L (< Pivot)", "R (≥ Pivot)", "Rückgabe"], rows)))
    res.highlights = [("sortiert", root.value)]
    return res
