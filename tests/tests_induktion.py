#!/usr/bin/env python3
"""Tests für dmatkit.rechnen.induktion (Semesterwoche 7): python3 tests/tests_induktion.py

Soll-Werte stammen aus Serie 7 (Aufgabenstellung), von Hand oder aus unabhängigem Python (Brute Force,
Schleifen, Iteration) — nie aus dem Ergebnis des Moduls selbst.
"""
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import dmatkit as dk
from dmatkit.rechnen import induktion as I
from dmatkit.rechnen.induktion import (coins, knight_walk, prove_divisible, prove_residue, prove_sum,
                                       quick_sort, tile_board)

N = [0]


def ok(cond, msg=""):
    N[0] += 1
    assert cond, msg


def eq(a, b, msg=""):
    N[0] += 1
    assert a == b, f"{msg}: {a!r} != {b!r}"


def raises(exc, fn, *a, text=None, **k):
    N[0] += 1
    try:
        fn(*a, **k)
    except exc as e:
        if text is not None:
            assert text in str(e), f"{text!r} nicht in {str(e)!r}"
        return e
    except Exception as e:
        raise AssertionError(f"{exc.__name__} erwartet, bekam {type(e).__name__}: {e}")
    raise AssertionError(f"{exc.__name__} erwartet, aber keine Ausnahme")


def shows(res):
    ok(isinstance(repr(res), str) and "Traceback" not in repr(res))
    ok(res._repr_html_().startswith("<style>") and isinstance(res.latex(), str))


# ==========================================================================
# 1. Summenformeln (Aufgaben 1 bis 4): richtige Formeln werden bewiesen, falsche nicht
# ==========================================================================
SERIE = [  # (Summand, Formel des Algorithmus, Grenzen)
    ("s + i*d", "n*s + n*(n-1)/2*d", dict(first=0, last="n-1")),      # Aufgabe 1
    ("s*q**i", "s*(q**n - 1)/(q - 1)", dict(first=0, last="n-1")),    # Aufgabe 2
    ("i**2", "n*(n+1)*(2*n+1)/6", {}),                                  # Aufgabe 3
    ("2*i - 1", "n**2", {}),                                            # Aufgabe 4
]
for term, closed, kw in SERIE:
    r = prove_sum(term, closed, **kw)
    ok(r.valid and r.anchor_ok and r.step_ok and r.difference == 0 and r.counterexample is None, closed)
    shows(r)
eq(prove_sum("2*i - 1", "n**2").title, "Schwache Induktion: Σ(i=1…n) [2*i - 1] = n**2")
ok(prove_sum("s*q**i", "s*(q**n - 1)/(q - 1)", first=0, last="n-1").warnings, "q = 1 teilt durch 0")


# Eine Summe unabhängig mit Schleife: stimmt die Formel für viele n?
def schleife(s, d, n):
    return sum(s + k * d for k in range(n))


ok(all(schleife(3, 2, n) == n * 3 + n * (n - 1) // 2 * 2 for n in range(0, 60)))
ok(all(sum(k * k for k in range(1, n + 1)) == n * (n + 1) * (2 * n + 1) // 6 for n in range(1, 60)))
ok(all(sum(2 * k - 1 for k in range(1, n + 1)) == n * n for n in range(1, 60)))
# falsche Formeln: kein Beweis, Gegenbeispiel aus der Probe
for term, closed, kw in [("i", "n*(n+1)/2 + 1", {}), ("i**2", "n*(n+1)/2", {}), ("2*i - 1", "n**2 + n", {}),
                         ("i", "n*(n-1)/2", {}), ("i**2", "n*(n+1)*(2*n+1)/5", {})]:
    r = prove_sum(term, closed, **kw)
    ok(not r.valid and r.counterexample is not None, closed)
    shows(r)
ok(prove_sum("i", "n*(n+1)/2 + 1").anchor_ok is False and prove_sum("i", "n*(n+1)/2 + 1").step_ok is True)   # nur Verankerung falsch
ok(prove_sum("i", "n*(n-1)/2").step_ok is False)                                                            # Schritt falsch
eq(prove_sum("i", "n*(n+1)/2", n0=3).n0, 3)
# Eingaben
raises(ValueError, prove_sum, "i", "n**2", last="2*n", text="um genau 1")
raises(ValueError, prove_sum, "i", "n**2", last="5")
raises(ValueError, prove_sum, "i", "n + i", text="nicht i")
raises(ValueError, prove_sum, "__import__('os')", "n")
raises(ValueError, prove_sum, "i", "n**(", text="gelesen")
raises(ValueError, prove_sum, "i", "n**5000", text="Exponent")
raises(ValueError, prove_sum, "i", "")
raises(ValueError, prove_sum, "i", "n", n0=-1)
raises(ValueError, prove_sum, "i", "n", n0=True)
raises(ValueError, prove_sum, "i", "n", first="n")
raises(ValueError, prove_sum, 1.5, "n")

# ==========================================================================
# 2. while-Schleifen, die nie enden (Aufgaben 5 bis 7)
# ==========================================================================
r = prove_divisible(8, 3, 5)
ok(r.valid and r.anchor_ok and r.step_ok and r.counterexample is None)
ok(all((8 ** n - 3 ** n) % 5 == 0 for n in range(0, 300)), "unabhängige Probe Aufgabe 5")
shows(r)
r = prove_residue(9, 10, [1, 9])
ok(r.valid and all(pow(9, n, 10) in (1, 9) for n in range(0, 300)), "Aufgabe 6")
shows(r)
r = prove_residue(2, 7, [1, 2, 4])
ok(r.valid and all(pow(2, n, 7) in (1, 2, 4) for n in range(0, 300)), "Aufgabe 7")
shows(r)
# Ähnliche Schleifen, die enden: Beweis scheitert, Gegenbeispiel stimmt mit echter Schleife überein
for a, m, rest in [(2, 7, [1, 2]), (3, 10, [1, 3]), (9, 10, [1])]:
    r = prove_residue(a, m, rest)
    n = 0
    while pow(a, n, m) in rest:
        n += 1
    ok(not r.valid and r.counterexample == n, (a, m, rest))
    shows(r)
r = prove_divisible(8, 3, 7)
ok(not r.valid and r.counterexample == 1 and (8 - 3) % 7 != 0)
r = prove_divisible(7, 2, 5, n0=0)
ok(r.valid and all((7 ** n - 2 ** n) % 5 == 0 for n in range(100)))
ok(prove_residue(9, 10, [9]).anchor_ok is False)
raises(ValueError, prove_residue, 1, 10, [1])
raises(ValueError, prove_residue, 9, 10, [])
raises(ValueError, prove_residue, 9, 10, [10], text="zwischen")
raises(ValueError, prove_residue, 9, 10, 5, text="Liste")
raises(ValueError, prove_residue, 9.5, 10, [1])
raises(ValueError, prove_divisible, 8, 3, 1)

# ==========================================================================
# 3. Parkettierung (Aufgabe 8): jedes Feld ausser dem freien genau einmal
# ==========================================================================
for n in (1, 2, 3, 4):
    size = 2 ** n
    holes = [(0, 0), (size - 1, size - 1), (0, size - 1), (size - 1, 0), (size // 2, size // 2 - 1)]
    for hole in holes:
        r = tile_board(n, hole)
        eq(r.tiles, (4 ** n - 1) // 3)
        felder = {}
        for rr in range(size):
            for cc in range(size):
                if (rr, cc) != hole:
                    felder.setdefault(r.grid[rr][cc], []).append((rr, cc))
        eq(r.grid[hole[0]][hole[1]], 0)
        ok(len(felder) == r.tiles and all(len(v) == 3 for v in felder.values()))
        ok(all(len({p[0] for p in v}) == 2 and len({p[1] for p in v}) == 2 for v in felder.values()), "Winkel, keine Linie")
        ok(all(max(p[0] for p in v) - min(p[0] for p in v) == 1 and max(p[1] for p in v) - min(p[1] for p in v) == 1 for v in felder.values()))
for hole in itertools.product(range(8), repeat=2):       # jedes Feld des 8×8-Bretts als Loch
    eq(tile_board(3, hole).tiles, 21)
shows(tile_board(2, (1, 2)))
shows(tile_board(5, (3, 4)))
ok(tile_board(3, (5, 2)).figure().axes)
raises(ValueError, tile_board, 0)
raises(ValueError, tile_board, 6)
raises(ValueError, tile_board, 2, (4, 0), text="Zeile, Spalte")
raises(ValueError, tile_board, 2, (0,))
raises(ValueError, tile_board, 2, "ab")
raises(ValueError, tile_board, True)

# ==========================================================================
# 4. Springerweg (Aufgabe 9)
# ==========================================================================
for n in range(4, 11):
    r = knight_walk(n)
    ok(set(r.path) == set(itertools.product(range(n), repeat=2)), n)
    ok(all(abs(a[0] - b[0]) * abs(a[1] - b[1]) == 2 for a, b in zip(r.path, r.path[1:])), n)
    eq(r.length, len(r.path) - 1)
shows(knight_walk(5))
raises(ValueError, knight_walk, 3, text="zwischen")
raises(ValueError, knight_walk, 13)
raises(ValueError, knight_walk, 4.0)

# ==========================================================================
# 5. Münzen (Aufgabe 10)
# ==========================================================================
for n in range(4, 400):
    c = coins(n)
    ok(c.a >= 0 and c.b >= 0 and 2 * c.a + 5 * c.b == n, n)
eq((coins(4).a, coins(4).b), (2, 0))
eq((coins(5).a, coins(5).b), (0, 1))
eq((coins(11).a, coins(11).b), (3, 1))
eq((coins(10 ** 6).a * 2 + coins(10 ** 6).b * 5), 10 ** 6)
shows(coins(4))
shows(coins(23))
raises(ValueError, coins, 3, text="zwischen")
raises(ValueError, coins, 4.5)
raises(ValueError, coins, True)
raises(ValueError, coins, 10 ** 6 + 1)
# kleinste Zahl ohne Zerlegung: 3 (und 1), darum n >= 4
ok(not any(2 * a + 5 * b == 3 for a in range(3) for b in range(3)))

# ==========================================================================
# 6. quickSort (Aufgabe 11)
# ==========================================================================
A = [4, 6, 5, 1, 7, 4, 3, 1]
for p in ("first", "middle", "last", "random"):
    r = quick_sort(A, pivot=p, seed=3)
    eq(r.value, sorted(A), p)
    ok(r.calls >= 3 and r.nodes[0] is r.root)
    shows(r)
rng = random.Random(11)
for _ in range(200):
    a = [rng.randint(-9, 9) for _ in range(rng.randint(1, 32))]
    eq(quick_sort(a, seed=rng.random()).value, sorted(a))
eq(quick_sort([5]).value, [5])
eq(quick_sort([2, 2, 2]).value, [2, 2, 2])
eq(quick_sort(A, pivot="first", seed=1).pivots[0], 4)
eq(quick_sort(A, seed=7).pivots, quick_sort(A, seed=7).pivots)             # reproduzierbar
ok(quick_sort(A, pivot="first").figure().axes and quick_sort(A).figure(values=True).axes)
raises(ValueError, quick_sort, [])
raises(ValueError, quick_sort, [1.5, 2])
raises(ValueError, quick_sort, "abc")
raises(ValueError, quick_sort, [1, 2], pivot="x")
raises(ValueError, quick_sort, list(range(33)))

# ==========================================================================
# 7. Zusammenspiel mit dem Paket
# ==========================================================================
ok(dk.WEEKS[7][1] is I and dk.induktion is I)
for name in I.__all__:
    ok(hasattr(dk, name), name)
ok("SW7" in dk.info() and "prove_sum" in dk.info() and "plot_tiling" in dk.info())
ok(dk.prove_sum("2*i-1", "n**2").valid and dk.coins(11).a == 3)
ok(set(I.INDUCTION_CODE) >= {"quickSort", "schleife_5", "schleife_6", "schleife_7"})
for k, code in I.INDUCTION_CODE.items():
    compile(code, k, "exec")                        # der Code der Serie ist gültiges Python

print(f"tests_induktion.py: alle grün ({N[0]} Prüfungen)")
