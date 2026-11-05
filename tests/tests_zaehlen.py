#!/usr/bin/env python3
"""Tests für dmatkit.rechnen.zaehlen (Semesterwoche 8): python3 tests/tests_zaehlen.py

Soll-Werte stammen aus den Beispielen der Serie 8 (Aufzählungen im Text), von Hand oder aus unabhängigem Python
(itertools-Aufzählung, Schleifen) — nie aus dem Ergebnis des Moduls selbst.
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import dmatkit as dk
from dmatkit.rechnen import zaehlen as Z
from dmatkit.rechnen.zaehlen import (assignment_rule, complement_rule, count_bitwords, count_combinations,
                                     count_permutations, count_subsets, count_surjections, count_variations,
                                     ip_network, lattice_paths, product_rule, sum_rule)

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
# 1. Zählprinzipien (Beispiele der Serie: A = {rot, grün, blau}, B = {schwarz, weiss})
# ==========================================================================
A, B = {"rot", "grün", "blau"}, {"schwarz", "weiss"}
eq(sum_rule(len(A), len(B)).count, len(A | B))
eq(product_rule(len(A), len(B)).count, len(list(itertools.product(A, B))))
eq(product_rule(3, 2, 5).count, 30)
eq(product_rule(2, 2, 2, 2).formula, "2^4")
eq(sum_rule(7).count, 7)
eq(sum_rule(0, 0).count, 0)
eq(product_rule(5, 0).count, 0)
eq(assignment_rule(12, 2).count, 6)
eq(assignment_rule(7).count, 7)
eq(complement_rule(100, 1).count, 99)
for res in (sum_rule(3, 2), product_rule(3, 2), assignment_rule(12, 2), assignment_rule(5), complement_rule(10, 4),
            product_rule(*[2] * 40), sum_rule(*range(20))):
    shows(res)
raises(ValueError, sum_rule, text="mindestens")
raises(ValueError, product_rule, text="mindestens")
raises(ValueError, sum_rule, -1)
raises(ValueError, product_rule, 2.5)
raises(ValueError, product_rule, True)
raises(ValueError, assignment_rule, 7, 2, text="teilbar")
raises(ValueError, assignment_rule, 7, 0)
raises(ValueError, complement_rule, 3, 4)

# ==========================================================================
# 2. Sechs fundamentale Zählprobleme: Beispiele der Serie (die Aufzählungen im PDF)
# ==========================================================================
eq(count_permutations(objects="abc").count, 6)                       # [a,b,c] … [c,b,a]
eq(count_permutations(objects="abc").items, sorted(set(itertools.permutations("abc"))))
eq(count_permutations(objects="aaabc").count, 20)                    # 20 Listen in der Serie
eq(count_permutations(repeats=[3, 1, 1]).count, 20)
eq(count_variations(objects="abcd", k=2).count, 12)                  # 12 Listen ohne Wiederholung
eq(count_variations(objects="abcd", k=2, repetition=True).count, 16)  # 16 Listen mit Wiederholung
eq(count_combinations(objects="abcde", k=3).count, 10)               # 10 Mengen
eq(count_combinations(objects="abcde", k=3, repetition=True).count, 35)   # 7 Zeilen zu 5 Mengen
for r in (count_permutations(objects="abc"), count_variations(objects="abcd", k=2), count_combinations(objects="abcde", k=3, repetition=True),
          count_permutations(objects="aaabc")):
    ok(r.checked and len(r.items) == r.count)
    shows(r)
# allgemein gegen itertools
for n in range(0, 9):
    eq(count_permutations(n).count, len(list(itertools.permutations(range(n)))), n)
    for k in range(0, n + 1):
        eq(count_variations(n, k).count, len(list(itertools.permutations(range(n), k))), (n, k))
        eq(count_combinations(n, k).count, len(list(itertools.combinations(range(n), k))), (n, k))
    for k in range(0, 5):
        eq(count_variations(n, k, repetition=True).count, len(list(itertools.product(range(n), repeat=k))), (n, k))
        eq(count_combinations(n, k, repetition=True).count, len(list(itertools.combinations_with_replacement(range(n), k))), (n, k))
# Permutationen mit Wiederholungen gegen Aufzählung
for word in ("aabb", "aabbb", "abcabc", "aaaa", "abcd", "aabbcc"):
    eq(count_permutations(objects=word).count, len(set(itertools.permutations(word))), word)
ok(count_variations(5, 2).checked and count_combinations(6, 3).checked)
eq(count_permutations(0).count, 1)
eq(count_variations(5, 0).count, 1)
eq(count_combinations(0, 0, repetition=True).count, 1)
eq(count_combinations(0, 2, repetition=True).count, 0)
raises(ValueError, count_variations, 3, 4, text="nur n = 3")
raises(ValueError, count_combinations, 3, 4)
raises(ValueError, count_permutations, 5, [2, 2], text="ergeben 4")
raises(ValueError, count_permutations, None, None)
raises(ValueError, count_permutations, repeats=[])
raises(ValueError, count_permutations, repeats=[0, 2])
raises(ValueError, count_variations, objects="aab", k=1)
raises(ValueError, count_permutations, 5001)
raises(ValueError, count_permutations, 2.5)

# ==========================================================================
# 3. Aufgaben der Serie 8: Werte von Hand / unabhängig
# ==========================================================================
eq(count_bitwords(8, ones=2).count, sum(1 for w in range(256) if bin(w).count("1") == 2))          # Aufgabe 1
eq(count_bitwords(8, ones=2).count, 28)
eq(count_bitwords(64, ones=2).count, 64 * 63 // 2)                                                  # Aufgabe 2: 2016
eq(count_bitwords(16).count, 2 ** 16)                                                               # Aufgabe 3: 65536
eq(count_bitwords(32, at_most=8).count, sum(math.comb(32, j) for j in range(9)))                    # Aufgabe 13
eq(count_bitwords(32, at_most=8).count, 15033173)
eq(count_bitwords(10, at_most=10).count, 2 ** 10)
eq(count_bitwords(5, ones=0).count, 1)
raises(ValueError, count_bitwords, 8, ones=9)
raises(ValueError, count_bitwords, 8, ones=1, at_most=2, text="nicht beides")
raises(ValueError, count_bitwords, -1)
eq(product_rule(*[62] * 7).count, 62 ** 7)                                                          # Aufgabe 4
eq(62 ** 7, 3521614606208)
eq(count_variations(16, 12, repetition=True).count, 16 ** 12)                                       # Aufgabe 5
eq(16 ** 12, 2 ** 48)
for n in range(0, 11):                                                                              # Aufgabe 6
    eq(count_subsets(n).count, sum(1 for k in range(n + 1) for _ in itertools.combinations(range(n), k)), n)
eq(count_subsets(objects=["schwarz", "weiss"]).count, 4)                                            # Beispiel der Serie
eq(len(count_subsets(objects=["schwarz", "weiss"]).items), 4)
ok(count_subsets(objects="ab").checked)
shows(count_subsets(objects="abc"))
shows(count_subsets(3))
eq(assignment_rule(1000 * 999, 2).count, math.comb(1000, 2))                                       # Aufgabe 7
eq(assignment_rule(1000 * 999, 2).count, 499500)
a8 = sum(62 ** k for k in range(6, 9))                                                              # Aufgabe 8a
eq(sum_rule(*[product_rule(*[62] * k).count for k in (6, 7, 8)]).count, a8)
b8 = complement_rule(a8, sum(52 ** k for k in range(6, 9))).count                                   # Aufgabe 8b
eq(b8, a8 - sum(52 ** k for k in range(6, 9)))
zeilen = product_rule(count_combinations(50, 5).count, count_combinations(12, 2).count).count       # Aufgabe 9
eq(zeilen, 139838160)
eq(zeilen * 29, 4055306640)
eq(count_combinations(4, 42, repetition=True).count, 14190)                                         # Aufgabe 10
eq(sum(1 for a in range(43) for b in range(43 - a) for c in range(43 - a - b)), math.comb(45, 3))   # a+b+c ≤ 42, vierter Prozessor = Rest
eq(product_rule(3, 3, 3, 3, 2, 2, 2).count, 648)                                                    # Aufgabe 11
pw = "a154bc0401011"
eq((pw.count("1"), pw.count("0")), (4, 3))
eq(3 ** pw.count("1") * 2 ** pw.count("0"), 648)
f = math.factorial
eq(count_permutations(repeats=[5, 9, 5, 3, 7]).count, f(29) // (f(5) * f(9) * f(5) * f(3) * f(7)))   # 12a
eq(len("EEEEAEACCEBEBBAACBDDBDBABCBCB"), 29)
eq(count_permutations(repeats=[1, 9, 5, 3, 7]).count, f(25) // (f(9) * f(5) * f(3) * f(7)))        # 12b
eq(count_permutations(5).count, 120)                                                                # 12c
# 12b und c an einem kleinen Beispiel (2 A, 2 B, 1 C) gegen Aufzählung
w = set(itertools.permutations("AABBC"))
eq(len(w), count_permutations(repeats=[2, 2, 1]).count)
eq(sum(1 for x in w if "AA" in "".join(x)), count_permutations(repeats=[1, 2, 1]).count)           # A-Block
eq(sum(1 for x in w if "AA" in "".join(x) and "BB" in "".join(x)), count_permutations(3).count)    # alle Blöcke: 3!
eq(sum(product_rule(a, b).count for a, b in ((10, 20), (20, 15), (15, 3))), 545)                    # Aufgabe 14a
eq(10 * 20 + 20 * 15 + 15 * 3, 545)
eq(product_rule(20, 15).count, 300)                                                                 # 14b
# Aufgabe 15 gegen Brute Force: ungerade 7-stellige Zahlen aus 1, 2, 3, 3, 0, 0, 0
zahlen = {int("".join(p)) for p in itertools.permutations("1233000") if p[0] != "0" and int(p[-1]) % 2 == 1}
eq(len(zahlen), 90)
fall1 = complement_rule(count_permutations(repeats=[1, 2, 3]).count, count_permutations(repeats=[1, 2, 2]).count).count   # Ende 1
fall3 = complement_rule(count_permutations(repeats=[1, 1, 1, 3]).count, count_permutations(repeats=[1, 1, 1, 2]).count).count   # Ende 3
eq(sum_rule(fall1, fall3).count, 90)
eq(count_variations(9, 6).count, 60480)                                                             # Aufgabe 16
eq(count_variations(50, 2).count, 2450)                                                             # Aufgabe 17
eq(product_rule(count_combinations(8, 5).count, count_variations(8, 5).count).count, 376320)        # Aufgabe 18
eq(count_variations(3, 9, repetition=True).count, 19683)                                            # 19a
eq(count_permutations(repeats=[3, 3, 3]).count, 1680)                                               # 19b
eq(count_surjections(9, 3).count, sum(1 for g in itertools.product(range(3), repeat=9) if len(set(g)) == 3))   # 19c
eq(count_surjections(9, 3).count, 18150)
eq(count_surjections(5, 5).count, 120)
eq(count_surjections(4, 2).count, 14)
eq(count_surjections(3, 4).count, 0)
raises(ValueError, count_surjections, 3, 0)
raises(ValueError, count_surjections, 401, 2)
shows(count_surjections(9, 3))
shows(count_surjections(20, 20))
eq(lattice_paths(6, 4).count, 210)                                                                  # Aufgabe 20a
eq(lattice_paths(6, 4, via=(2, 2)).count, 90)                                                       # 20b
eq(lattice_paths(0, 5).count, 1)
eq(lattice_paths(6, 4, via=(6, 4)).count, 210)
eq(lattice_paths(6, 4, via=(0, 0)).count, 210)
raises(ValueError, lattice_paths, 6, 4, via=(7, 0))
raises(ValueError, lattice_paths, 6, 4, via=(1,))
shows(lattice_paths(6, 4))
shows(lattice_paths(6, 4, via=(2, 2)))


def ringe(n):
    """Ringanordnungen bis auf Drehen und Spiegeln, durch Aufzählen."""
    seen = set()
    for p in itertools.permutations(range(n)):
        seen.add(min(min(q[i:] + q[:i] for i in range(n)) for q in (p, p[::-1])))
    return len(seen)


for n in (3, 4, 5, 6, 7):                                                                           # Aufgabe 21
    eq(ringe(n), assignment_rule(f(n), 2 * n).count, n)
eq(assignment_rule(f(10), 20).count, 181440)
eq(f(9) // 2, 181440)
eq(count_variations(2, 32, repetition=True).count, 4294967296)                                      # 22a
eq(ip_network("186.13.157.160/27").hosts, 30)                                                       # 22b
eq(count_variations(2, 128, repetition=True).count, 340282366920938463463374607431768211456)        # 22c
shows(count_variations(2, 128, repetition=True))

# ==========================================================================
# 4. IPv4-Teilnetz (Beispiel der Serie: 191.0.13.143/26)
# ==========================================================================
r = ip_network("191.0.13.143/26")
eq((r.network, r.broadcast, r.first_host, r.last_host, r.hosts), ("191.0.13.128", "191.0.13.191", "191.0.13.129", "191.0.13.190", 62))
eq(r.prefix, 26)
shows(r)
eq(ip_network("186.13.157.160/27").network, "186.13.157.160")
eq(ip_network("186.13.157.160/27").broadcast, "186.13.157.191")
eq(ip_network("10.0.0.0/8").hosts, 2 ** 24 - 2)
eq(ip_network("192.168.1.77/24").first_host, "192.168.1.1")
for bad in ("191.0.13.143", "300.1.1.1/8", "1.2.3.4/33", "1.2.3.4/31", "abc/8", "::1/64", "1.2.3.4/"):
    raises(ValueError, ip_network, bad)
raises(ValueError, ip_network, 5)

# ==========================================================================
# 5. Zusammenspiel mit dem Paket
# ==========================================================================
ok(dk.WEEKS[8][1] is Z and dk.zaehlen is Z)
for name in Z.__all__:
    ok(hasattr(dk, name), name)
ok("SW8" in dk.info() and "count_combinations" in dk.info())
ok(dk.count_bitwords(8, ones=2).count == 28 and dk.ip_network("191.0.13.143/26").hosts == 62)

print(f"tests_zaehlen.py: alle grün ({N[0]} Prüfungen)")
