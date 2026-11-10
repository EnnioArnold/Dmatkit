#!/usr/bin/env python3
"""Tests für dmatkit.rechnen.zaehlkomplex (Semesterwoche 9): python3 tests/tests_zaehlkomplex.py

Soll-Werte stammen aus den Beispielen der Serie 9 (Seiten 1, 2, 12) oder aus unabhängigem Python
(itertools-Aufzählung, Schleifen) — nie aus dem Ergebnis des Moduls selbst.
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import dmatkit as dk
from dmatkit.rechnen import zaehlkomplex as Z
from dmatkit.rechnen.zaehlkomplex import (count_divisible, count_fixed_point, count_recursive, count_unused,
                                          gf_coins, gf_count, inclusion_exclusion)

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
        return
    raise AssertionError(f"{exc.__name__} erwartet")


def shows(res):
    ok(isinstance(repr(res), str) and res._repr_html_().startswith("<style>") and isinstance(res.latex(), str))


# 1. Inklusion und Exklusion: Beispiele der Serie (Seite 1 und 2)
pin1 = {f"{n:04d}" for n in range(10000) if len(set(f"{n:04d}"[:3])) == 1}
pin2 = {f"{n:04d}" for n in range(10000) if len(set(f"{n:04d}"[1:])) == 1}
r = inclusion_exclusion([pin1, pin2])
eq((r.summe, r.exklusion, r.inklusion, r.count), (200, 10, 0, 190), "PIN-Beispiel: 100 + 100 - 10")
r = inclusion_exclusion([{1, 4, 5, 7}, {2, 4, 6, 7}, {3, 5, 6, 7}])
eq((r.summe, r.inklusion, r.exklusion, r.count), (12, 1, 6, 7), "drei Mengen: 4+4+4-2-2-2+1")
ok(r.checked)
shows(r)
eq(inclusion_exclusion([{1, 2}]).count, 2)
eq(inclusion_exclusion([{1, 2}, {3}]).count, 3, "disjunkt: Summenregel")
raises(ValueError, inclusion_exclusion, [])
raises(ValueError, inclusion_exclusion, [{1}] * 13)
# Zufallsproben gegen die direkte Vereinigung
import random
rng = random.Random(5)
for _ in range(60):
    ss = [set(rng.sample(range(20), rng.randint(0, 12))) for _ in range(rng.randint(1, 6))]
    eq(inclusion_exclusion(ss).count, len(set().union(*ss)))

# 2. Teilbare Zahlen
eq(count_divisible(10, [2, 3]).count, 7, "2, 3, 4, 6, 8, 9, 10")
for lim, ds in [(1000, [2, 3, 5]), (10000, [6, 7, 8]), (100000, [2, 3, 5, 7]), (50, [4, 6]), (30, [3, 3]), (5, [7])]:
    soll = sum(1 for m in range(1, lim + 1) if any(m % d == 0 for d in ds))
    r = count_divisible(lim, ds)
    eq(r.count, soll, f"{lim} {ds}")
    eq(r.complement, lim - soll)
shows(count_divisible(1000, [2, 3, 5]))
eq(count_divisible(210 * 10 ** 6, [2, 3, 5, 7]).complement, 48 * 10 ** 6, "teilerfremd zu 210: φ(210) = 48 je Block, grosse Grenze ohne Aufzählen")
raises(ValueError, count_divisible, 10, [])
raises(ValueError, count_divisible, 10, [0])
raises(ValueError, count_divisible, 0, [2])

# 3. Siebformel
for n in range(1, 8):
    soll = sum(1 for p in itertools.permutations(range(n)) if any(p[i] == i for i in range(n)))
    eq(count_fixed_point(n).count, soll, f"Fixpunkt n={n}")
eq(count_fixed_point(8).count, 25487)
eq(count_fixed_point(8).complement, 14833, "Derangements D8")
for n, m in [(7, 5), (4, 3), (3, 3), (2, 4), (0, 2)]:
    soll = sum(1 for f in itertools.product(range(m), repeat=n) if len(set(f)) < m)
    r = count_unused(n, m)
    eq(r.count, soll, f"{n} Aufträge, {m} Drucker")
    eq(r.complement, dk.count_surjections(n, m).count, "Gegenteil = Surjektionen")
shows(count_unused(7, 5))

# 4. Rekursion
kein = lambda n, w: sum(1 for x in itertools.product("01", repeat=n) if w not in "".join(x))
eq([count_recursive("no00", n).count for n in range(1, 13)], [kein(n, "00") for n in range(1, 13)])
eq([count_recursive("no000", n).count for n in range(1, 13)], [kein(n, "000") for n in range(1, 13)])
eq([count_recursive("contains01", n).count for n in range(1, 13)], [2 ** n - kein(n, "01") for n in range(1, 13)])
eq([count_recursive("even_zeros", n).count for n in range(1, 5)],
   [sum(1 for w in itertools.product("0123456789", repeat=n) if w.count("0") % 2 == 0) for n in range(1, 5)])
eq([count_recursive("stairs", n).count for n in range(1, 11)], [1, 2, 3, 5, 8, 13, 21, 34, 55, 89])
eq(count_recursive("no00", 3).count, 5, "000 und 001 fehlen: 010, 011, 101, 110, 111")
eq(count_recursive("even_zeros", 1).count, 9)
eq(count_recursive("no00", 200).count, Z._fib(202), "grosses n: Fibonacci")
eq(count_recursive("contains01", 300).count, 2 ** 300 - 301)
ok(count_recursive("stairs", 10).values[10] == 89 and "s(n−1)" in count_recursive("stairs", 4).recurrence)
shows(count_recursive("no000", 8))
raises(ValueError, count_recursive, "quatsch", 3, text="Unbekanntes Problem")
raises(ValueError, count_recursive, "no00", 0)

# 5. Erzeugende Funktionen: Beispiel von Seite 12
r = gf_count([[2, 3, 4], [3, 4], [4, 5]], 11)
eq(dict(sorted(r.poly.items())), {9: 1, 10: 3, 11: 4, 12: 3, 13: 1}, "x^9 + 3x^10 + 4x^11 + 3x^12 + x^13")
eq(r.count, 4)
eq(gf_count([range(1, 7)] * 4, 13).count, sum(1 for c in itertools.product(range(1, 7), repeat=4) if sum(c) == 13))
eq(gf_count([range(2, 5)] * 3, 8).count, 6)
eq(gf_count([[1, 2]], 5).count, 0, "Summe nicht erreichbar")
shows(r)
raises(ValueError, gf_count, [], 3)
raises(ValueError, gf_count, [[]], 3)

# 6. Münzen
eq(gf_coins([1, 2, 5], 15).count, sum(1 for a in range(16) for b in range(8) for c in range(4) if a + 2 * b + 5 * c == 15))
seq = lambda n: 1 if n == 0 else sum(seq(n - c) for c in (1, 2, 5) if c <= n)
eq(gf_coins([1, 2, 5], 15, ordered=True).count, seq(15))
eq([gf_coins([1, 2], t, ordered=True).count for t in range(1, 9)], [1, 2, 3, 5, 8, 13, 21, 34], "Treppe als Münzen 1, 2")
eq(gf_coins([3], 7).count, 0)
eq(gf_coins([3], 0).count, 1, "Betrag 0: die leere Zahlung")
shows(gf_coins([1, 2, 5], 15, ordered=True))
raises(ValueError, gf_coins, [], 5)

# 7. Registrierung
ok(dk.count_divisible is count_divisible and dk.WEEKS[9][1] is Z and "gf_coins" in dk.info())
ok(dk.zaehlkomplex is Z and "zaehlen" in dk.WEEKS[8][1].__name__)

print(f"tests_zaehlkomplex.py: {N[0]} Prüfungen bestanden")
