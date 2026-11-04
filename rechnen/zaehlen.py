#!/usr/bin/env python3
"""
Grundlegende Zähltechniken (Semesterwoche 8, Serie 8).

Was hier steht (alles exakt mit ganzen Zahlen gerechnet; wo es klein genug ist, wird jedes Ergebnis
zusätzlich durch Aufzählen aller Möglichkeiten geprüft):

  Die drei Zählprinzipien
    sum_rule(*sizes)                    Summenregel: |A ∪ B| = |A| + |B| für disjunkte Mengen
    product_rule(*sizes)                Produktregel: |S₁ × … × Sₙ| = |S₁| · … · |Sₙ|
    assignment_rule(size_a, k)          Zuordnungsregel: jedes Element von B genau k-mal getroffen: |B| = |A| / k
    complement_rule(total, excluded)    Gesamtmenge minus Gegenteil (folgt aus der Summenregel)

  Die sechs fundamentalen Zählprobleme
    count_permutations(...)             Permutationen: n!  oder  n!/(s₁!·…·s_k!)
    count_variations(n, k, repetition)  Variationen: n!/(n−k)!  oder  nᵏ
    count_combinations(n, k, repetition) Kombinationen: C(n, k)  oder  C(n+k−1, k)

  Hilfen für die Aufgaben
    count_bitwords(n, ones, at_most)    Bitwörter der Länge n mit genau oder höchstens k Einsen
    count_subsets(n)                    Potenzmenge: |P(A)| = 2ⁿ (Zuordnung zu Bitwörtern)
    count_surjections(n, m)             n verschiedene Objekte auf m Fächer, jedes Fach belegt
    lattice_paths(right, up, via)       kürzeste Wege im Gitter (Aufgabe 20)
    ip_network(cidr)                    IPv4-Teilnetz: Netzname, Broadcast, Hostbereich, Anzahl Hosts (Aufgabe 22)

Hinweise zu den Unterlagen (auch im Abschlussbericht vermerkt):
  * Die PDF-Serie 8 enthält nur die Aufgabenstellungen, keine Lösungen. Alle Resultate sind eigene Rechnungen.
  * Aufgabe 14 b (»Wege von einem Neuron im Input Layer zu einem Neuron im Output Layer«): gerechnet wird
    für ein festes Neuronenpaar, 20·15 = 300. TODO: mit der Vorlesung abgleichen (alle Paare: 10·300·3 = 9000).
  * Aufgabe 21 (Ringtopologie): Ringe, die sich nur durch Drehen oder Spiegeln unterscheiden, sind dieselbe
    Anordnung: 10!/(10·2) = 181 440. Zählt man die Richtung mit, wären es 9! = 362 880. TODO: abgleichen.
  * Aufgabe 11: gefragt ist die Zahl aller Möglichkeiten (648); mit dem richtigen Passwort darunter wären
    höchstens 648 Versuche nötig.
  * Aufgabe 19 c braucht die Siebformel (nicht in der Serie): n Objekte auf m Fächer ohne leeres Fach.
"""

from __future__ import annotations

import ipaddress
import itertools
import math

from .render import Result, Step, Table

# ==========================================================================
# Grenzen
# ==========================================================================

MAX_N = 5000                   # grösste Objektzahl n (n! bleibt exakt rechenbar)
MAX_SUMMANDS = 10_000
MAX_BRUTE = 200_000            # so viele Möglichkeiten werden höchstens zur Probe aufgezählt
MAX_LIST = 60                  # Zeilen in der Aufzählung

__all__ = ["CountResult", "sum_rule", "product_rule", "assignment_rule", "complement_rule",
           "count_permutations", "count_variations", "count_combinations", "count_bitwords",
           "count_subsets", "count_surjections", "lattice_paths", "NetworkResult", "ip_network"]


# ==========================================================================
# Hilfen
# ==========================================================================

def _fmt(v: int) -> str:
    """Ganze Zahl mit Hochkomma als Tausendertrenner (Schweizer Schreibweise); sehr lange Zahlen gekürzt."""
    s = f"{v:,}".replace(",", "’")
    if len(str(abs(v))) > 60:
        e = len(str(abs(v))) - 1
        return f"{s[:6]}… ≈ {str(abs(v))[0]},{str(abs(v))[1:4]}·10^{e}"
    return s


def _int(v, name, lo=0, hi=MAX_N) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name} muss eine ganze Zahl sein, nicht {v!r}")
    if not lo <= v <= hi:
        raise ValueError(f"{name} muss zwischen {lo} und {hi} liegen")
    return v


class CountResult(Result):
    """
    ``count`` (die Anzahl), ``formula`` (Text der Formel), ``items`` (alle Möglichkeiten, wenn sie aufgezählt wurden,
    sonst None), ``checked`` (True, wenn ``count`` durch Aufzählen bestätigt wurde).
    """
    count = 0
    formula = ""
    items = None
    checked = False

    def _finish(self, label: str = "Anzahl"):
        self.highlights = [(label, self.count)]
        return self


def _enumeration_step(res: CountResult, items: list, header: str, what: str):
    shown = items if len(items) <= MAX_LIST else items[:MAX_LIST // 2] + [None] + items[-(MAX_LIST // 2 - 1):]
    rows = [["…"] if it is None else ["".join(map(str, it)) if all(isinstance(x, str) and len(x) == 1 for x in it) else str(list(it))] for it in shown]
    res.steps.append(Step("Probe durch Aufzählen", f"Alle {len(items)} {what} aufgeschrieben; die Anzahl stimmt mit der Formel überein.",
                          table=Table([header], rows)))
    res.items, res.checked = items, True


# ==========================================================================
# Die drei Zählprinzipien
# ==========================================================================

def sum_rule(*sizes: int) -> CountResult:
    """
    Summenregel: Sind die endlichen Mengen S₁, …, Sₙ paarweise disjunkt, so gilt |S₁ ∪ … ∪ Sₙ| = |S₁| + … + |Sₙ|.

    >>> sum_rule(3, 2).count
    5
    """
    if not sizes or len(sizes) > MAX_SUMMANDS:
        raise ValueError("Die Summenregel braucht mindestens eine Mengengrösse")
    s = [_int(v, "Mengengrösse", 0, 10 ** 400) for v in sizes]
    res = CountResult()
    res.count = sum(s)
    res.formula = " + ".join(map(str, s))
    res.title = "Summenregel: " + (res.formula if len(s) <= 8 else f"Summe von {len(s)} Mengen")
    res.summary = "Die Mengen sind paarweise disjunkt (Partition der Gesamtmenge)."
    res.steps.append(Step("Voraussetzung", "Die Mengen S₁, …, Sₙ haben kein gemeinsames Element, jedes Element liegt in genau einer.",
                          rule="Summenregel"))
    res.steps.append(Step("Rechnung", "|S| = |S₁| + |S₂| + … + |Sₙ|",
                          items=[("|S|", (res.formula + f" = {_fmt(res.count)}") if len(s) <= 8 else _fmt(res.count))], rule="Summenregel"))
    return res._finish()


def product_rule(*sizes: int) -> CountResult:
    """
    Produktregel: |S₁ × … × Sₙ| = |S₁| · … · |Sₙ|. Bei lauter gleichen Mengen: |Sⁿ| = |S|ⁿ.

    >>> product_rule(3, 2).count
    6
    >>> product_rule(62, 62, 62).count
    238328
    """
    if not sizes or len(sizes) > MAX_SUMMANDS:
        raise ValueError("Die Produktregel braucht mindestens eine Mengengrösse")
    s = [_int(v, "Mengengrösse", 0, 10 ** 400) for v in sizes]
    res = CountResult()
    res.count = math.prod(s)
    same = len(set(s)) == 1 and len(s) > 1
    res.formula = f"{s[0]}^{len(s)}" if same else " · ".join(map(str, s))
    res.title = "Produktregel: " + (res.formula if len(s) <= 8 or same else f"Produkt von {len(s)} Mengen")
    res.summary = "An jeder Stelle der Liste wird unabhängig ein Element gewählt."
    res.steps.append(Step("Voraussetzung", "Jede Liste [x₁, …, xₙ] hat an Stelle i ein Element aus Sᵢ, unabhängig von den anderen Stellen.",
                          rule="Produktregel"))
    res.steps.append(Step("Rechnung", "|S₁ × … × Sₙ| = |S₁| · … · |Sₙ|" + (f"  =  |S|ⁿ mit |S| = {s[0]}, n = {len(s)}" if same else ""),
                          items=[("Anzahl", f"{res.formula} = {_fmt(res.count)}" if (len(s) <= 8 or same) else _fmt(res.count))], rule="Produktregel"))
    return res._finish()


def assignment_rule(size_a: int, k: int = 1) -> CountResult:
    """
    Zuordnungsregel: Trifft eine surjektive Abbildung f: A → B jedes Element von B genau k-mal, so gilt |B| = |A| / k.
    Für k = 1 ist f bijektiv und |B| = |A|.

    >>> assignment_rule(12, 2).count
    6
    """
    a = _int(size_a, "|A|", 0, 10 ** 400)
    k = _int(k, "k", 1, 10 ** 400)
    if a % k:
        raise ValueError(f"|A| = {a} ist nicht durch k = {k} teilbar: keine Abbildung, die jedes Element von B genau {k}-mal trifft")
    res = CountResult()
    res.count = a // k
    res.formula = f"{a} / {k}"
    res.title = f"Zuordnungsregel: |B| = |A| / k = {_fmt(a)} / {k}" if k > 1 else f"Zuordnungsregel (bijektiv): |B| = |A| = {_fmt(a)}"
    res.summary = "Es gibt eine Abbildung A → B, die jedes Element von B genau k-mal trifft."
    res.steps.append(Step("Voraussetzung", f"f: A → B ist surjektiv, und jedes Element von B kommt genau {k}-mal als Output vor." if k > 1
                          else "f: A → B ist bijektiv: jedes Element von B kommt genau einmal als Output vor.", rule="Zuordnungsregel"))
    res.steps.append(Step("Rechnung", "|A| = k·|B|, also |B| = |A| / k.", items=[("|B|", f"{_fmt(a)} / {k} = {_fmt(res.count)}")], rule="Zuordnungsregel"))
    return res._finish()


def complement_rule(total: int, excluded: int) -> CountResult:
    """
    Gegenteil zählen: Ist S die Gesamtmenge und E die Menge der unerwünschten Elemente, so ist |S \\ E| = |S| − |E|
    (Summenregel: |S| = |E| + |S \\ E|).

    >>> complement_rule(10, 4).count
    6
    """
    t = _int(total, "Gesamtzahl", 0, 10 ** 400)
    e = _int(excluded, "unerwünschte Zahl", 0, 10 ** 400)
    if e > t:
        raise ValueError("Es kann nicht mehr Elemente ausserhalb geben als insgesamt")
    res = CountResult()
    res.count = t - e
    res.formula = f"{t} − {e}"
    res.title = f"Gegenteil zählen: {_fmt(t)} − {_fmt(e)} = {_fmt(t - e)}"
    res.summary = "Statt der gesuchten Menge zählt man alle und zieht das Gegenteil ab."
    res.steps.append(Step("Idee", "Alle Möglichkeiten zerfallen in die gesuchten und die ungewünschten (disjunkt): |S| = |gesucht| + |ungewünscht|.",
                          rule="Summenregel"))
    res.steps.append(Step("Rechnung", "|gesucht| = |S| − |ungewünscht|", items=[("Anzahl", f"{_fmt(t)} − {_fmt(e)} = {_fmt(res.count)}")]))
    return res._finish()


# ==========================================================================
# Die sechs fundamentalen Zählprobleme
# ==========================================================================

def count_permutations(n: int | None = None, repeats=None, objects=None) -> CountResult:
    """
    Permutationen: alle Objekte in einer Reihenfolge. Paarweise verschieden: n!. Mit Wiederholungen
    (``repeats`` = [s₁, …, s_k], Summe = n): n!/(s₁!·…·s_k!).

    ``objects`` (Text oder Liste, etwa ``"aaabc"``) liefert n und die Wiederholungen von selbst und zählt zur Probe alle auf.

    >>> count_permutations(3).count
    6
    >>> count_permutations(objects="aaabc").count
    20
    >>> count_permutations(repeats=[2, 1, 1]).count
    12
    """
    if objects is not None:
        objs = list(objects)
        if not objs or len(objs) > 12:
            raise ValueError("objects: 1 bis 12 Objekte (sonst nur über n und repeats)")
        reps = sorted(objs.count(x) for x in set(objs))
        n, repeats = len(objs), (None if set(reps) == {1} else reps)
    if repeats is not None:
        if not isinstance(repeats, (list, tuple)) or not repeats:
            raise ValueError("repeats: eine Liste wie [3, 1, 1]")
        reps = [_int(r, "Wiederholung", 1, MAX_N) for r in repeats]
        if n is not None and n != sum(reps):
            raise ValueError(f"Die Wiederholungen ergeben {sum(reps)} Objekte, nicht n = {n}")
        n = sum(reps)
    n = _int(n, "n", 0, MAX_N)
    res = CountResult()
    if repeats is None or all(r == 1 for r in (repeats or [])):
        res.count = math.factorial(n)
        res.formula = f"{n}!"
        res.title = f"Permutationen von {n} verschiedenen Objekten"
        res.steps.append(Step("Fall", f"Alle {n} Objekte sind paarweise verschieden und werden in eine Reihenfolge gebracht.", rule="Permutation"))
        res.steps.append(Step("Formel", "n! = n · (n−1) · … · 2 · 1", items=[("Anzahl", f"{n}! = {_fmt(res.count)}")], rule="Permutation ohne Wiederholung"))
    else:
        reps = [int(r) for r in repeats]
        res.count = math.factorial(n) // math.prod(math.factorial(r) for r in reps)
        res.formula = f"{n}!/(" + "·".join(f"{r}!" for r in reps) + ")"
        res.title = f"Permutationen mit Wiederholungen: n = {n}, Wiederholungen {reps}"
        res.steps.append(Step("Fall", f"{n} Objekte, von denen gleiche mehrfach vorkommen: {', '.join(map(str, reps))} Mal.", rule="Permutation"))
        res.steps.append(Step("Formel", "n!/(s₁!·s₂!·…·s_k!): Jede Anordnung mit gleichen Objekten entsteht aus s₁!·s₂!·…·s_k! Anordnungen "
                              "mit nummerierten Objekten (Zuordnungsregel).", items=[("Anzahl", f"{res.formula} = {_fmt(res.count)}")],
                              rule="Permutation mit Wiederholungen"))
    res.summary = f"{_fmt(res.count)} Permutationen."
    if objects is not None:
        _enumeration_step(res, sorted(set(itertools.permutations(objs))), "Permutation", "Permutationen")
        if len(res.items) != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
    return res._finish()


def count_variations(n: int | None = None, k: int | None = None, repetition: bool = False, objects=None) -> CountResult:
    """
    Variationen: k von n Objekten auswählen und in eine Reihenfolge bringen. Ohne Wiederholungen n!/(n−k)!,
    mit Wiederholungen nᵏ. ``objects`` (etwa ``"abcd"``) zählt zur Probe alle auf.

    >>> count_variations(4, 2).count
    12
    >>> count_variations(4, 2, repetition=True).count
    16
    """
    if objects is not None:
        objs = list(objects)
        if len(set(objs)) != len(objs) or not 1 <= len(objs) <= 10:
            raise ValueError("objects: 1 bis 10 verschiedene Objekte")
        n = len(objs)
    n, k = _int(n, "n", 0, MAX_N), _int(k, "k", 0, MAX_N)
    if not repetition and k > n:
        raise ValueError(f"Ohne Wiederholung kann man nicht k = {k} von nur n = {n} Objekten wählen")
    res = CountResult()
    if repetition:
        res.count = n ** k
        res.formula = f"{n}^{k}"
        res.title = f"Variationen mit Wiederholungen: k = {k} aus n = {n}"
        res.steps.append(Step("Fall", f"{k} Stellen, an jeder wird eines von {n} Objekten gewählt; Objekte dürfen mehrfach vorkommen. Reihenfolge zählt.",
                              rule="Variation"))
        res.steps.append(Step("Formel", "nᵏ (Produktregel mit k gleichen Mengen)", items=[("Anzahl", f"{res.formula} = {_fmt(res.count)}")],
                              rule="Variation mit Wiederholungen"))
    else:
        res.count = math.perm(n, k)
        res.formula = f"{n}!/({n}−{k})!"
        res.title = f"Variationen ohne Wiederholungen: k = {k} aus n = {n}"
        prod = " · ".join(str(n - j) for j in range(min(k, 6))) + (" · …" if k > 6 else "")
        res.steps.append(Step("Fall", f"{k} von {n} verschiedenen Objekten, jedes höchstens einmal, in einer Reihenfolge.", rule="Variation"))
        res.steps.append(Step("Formel", "n!/(n−k)! = n · (n−1) · … · (n−k+1) (Produktregel: an Stelle i bleiben n−i+1 Objekte)",
                              items=[("Anzahl", (f"{prod} = " if k else "") + _fmt(res.count))], rule="Variation ohne Wiederholungen"))
    res.summary = f"{_fmt(res.count)} Variationen."
    if objects is not None:
        items = list(itertools.product(objs, repeat=k)) if repetition else list(itertools.permutations(objs, k))
        _enumeration_step(res, items, "Variation", "Variationen")
        if len(items) != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
    elif res.count <= MAX_BRUTE:
        # Probe ohne Aufzählung der Elemente: Zähle nach
        cnt = sum(1 for _ in (itertools.product(range(n), repeat=k) if repetition else itertools.permutations(range(n), k)))
        if cnt != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
    return res._finish()


def count_combinations(n: int | None = None, k: int | None = None, repetition: bool = False, objects=None) -> CountResult:
    """
    Kombinationen: k von n Objekten auswählen, Reihenfolge egal. Ohne Wiederholungen C(n, k) = n!/(k!·(n−k)!),
    mit Wiederholungen C(n+k−1, k). ``objects`` (etwa ``"abcde"``) zählt zur Probe alle auf.

    >>> count_combinations(5, 3).count
    10
    >>> count_combinations(5, 3, repetition=True).count
    35
    """
    if objects is not None:
        objs = list(objects)
        if len(set(objs)) != len(objs) or not 1 <= len(objs) <= 12:
            raise ValueError("objects: 1 bis 12 verschiedene Objekte")
        n = len(objs)
    n, k = _int(n, "n", 0, MAX_N), _int(k, "k", 0, MAX_N)
    if not repetition and k > n:
        raise ValueError(f"Ohne Wiederholung kann man nicht k = {k} von nur n = {n} Objekten wählen")
    res = CountResult()
    if repetition:
        top = n + k - 1
        res.count = math.comb(top, k) if n else (1 if k == 0 else 0)
        res.formula = f"C({top}, {k})"
        res.title = f"Kombinationen mit Wiederholungen: k = {k} aus n = {n}"
        res.steps.append(Step("Fall", f"Aus {n} Sorten werden {k} Stück gewählt; eine Sorte darf mehrfach vorkommen, die Reihenfolge ist egal.", rule="Kombination"))
        res.steps.append(Step("Formel", "C(n+k−1, k) = (n+k−1)!/(k!·(n−1)!) (k Stück und n−1 Trennstriche in beliebiger Reihenfolge)",
                              items=[("Anzahl", f"{top}!/({k}!·{n - 1}!) = {_fmt(res.count)}" if n else _fmt(res.count))], rule="Kombination mit Wiederholungen"))
    else:
        res.count = math.comb(n, k)
        res.formula = f"C({n}, {k})"
        res.title = f"Kombinationen ohne Wiederholungen: k = {k} aus n = {n}"
        res.steps.append(Step("Fall", f"{k} von {n} verschiedenen Objekten, jedes höchstens einmal, die Reihenfolge ist egal.", rule="Kombination"))
        res.steps.append(Step("Formel", "C(n, k) = n!/(k!·(n−k)!): die Variationen n!/(n−k)! zählen jede Auswahl k!-mal (Zuordnungsregel).",
                              items=[("Anzahl", f"{n}!/({k}!·{n - k}!) = {_fmt(res.count)}")], rule="Kombination ohne Wiederholungen"))
    res.summary = f"{_fmt(res.count)} Kombinationen."
    if objects is not None:
        items = list(itertools.combinations_with_replacement(objs, k) if repetition else itertools.combinations(objs, k))
        _enumeration_step(res, items, "Kombination", "Kombinationen")
        if len(items) != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
    elif res.count <= MAX_BRUTE and n <= 30 and k <= 30:
        gen = itertools.combinations_with_replacement(range(n), k) if repetition else itertools.combinations(range(n), k)
        if sum(1 for _ in gen) != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
    return res._finish()


# ==========================================================================
# Hilfen für die Aufgaben
# ==========================================================================

def count_bitwords(n: int, ones: int | None = None, at_most: int | None = None) -> CountResult:
    """
    Bitwörter der Länge n mit genau ``ones`` Einsen: C(n, k) (Serie 8, Aufgaben 1 und 2), oder mit höchstens ``at_most`` Einsen:
    Summe über j = 0 … k von C(n, j) (Aufgabe 13). Ohne beides: alle 2ⁿ Bitwörter (Aufgabe 3).

    >>> count_bitwords(8, ones=2).count
    28
    >>> count_bitwords(16).count
    65536
    """
    n = _int(n, "n", 0, MAX_N)
    if ones is not None and at_most is not None:
        raise ValueError("Entweder ones oder at_most, nicht beides")
    res = CountResult()
    if ones is None and at_most is None:
        res.count = 2 ** n
        res.title = f"Bitwörter der Länge {n}"
        res.steps.append(Step("Produktregel", f"Jede der {n} Stellen ist 0 oder 1.", items=[("Anzahl", f"2^{n} = {_fmt(res.count)}")], rule="Produktregel"))
        res.formula = f"2^{n}"
        res.summary = f"{_fmt(res.count)} Bitwörter."
        res.checked = n <= 16 and sum(1 for _ in itertools.product((0, 1), repeat=n)) == res.count
        return res._finish()
    k = _int(ones if ones is not None else at_most, "k", 0, n)
    if ones is not None:
        res.count = math.comb(n, k)
        res.formula = f"C({n}, {k})"
        res.title = f"Bitwörter der Länge {n} mit genau {k} Einsen"
        res.steps.append(Step("Fall", f"Die {k} Stellen mit einer 1 festlegen; die übrigen {n - k} Stellen sind dann 0. Jedes solche Wort gehört zu "
                              f"genau einer {k}-elementigen Teilmenge der {n} Stellen (Zuordnungsregel, k = 1).", rule="Zuordnungsregel"))
        res.steps.append(Step("Formel", "Kombinationen ohne Wiederholungen", items=[("Anzahl", f"{res.formula} = {_fmt(res.count)}")], rule="Kombination ohne Wiederholungen"))
        probe = (lambda w: bin(w).count("1") == k)
    else:
        parts = [math.comb(n, j) for j in range(k + 1)]
        res.count = sum(parts)
        res.formula = f"Σ_(j=0..{k}) C({n}, j)"
        res.title = f"Bitwörter der Länge {n} mit höchstens {k} Einsen"
        res.steps.append(Step("Partition", f"Nach der Anzahl j der Einsen aufteilen, j = 0 … {k}: die Teilmengen sind paarweise disjunkt.", rule="Summenregel"))
        shown = [[str(j), f"C({n}, {j})", _fmt(p)] for j, p in enumerate(parts)]
        res.steps.append(Step("Summe", "Je Teilmenge C(n, j) (Bitwörter mit genau j Einsen), dann addieren.",
                              table=Table(["j", "Anzahl", "Wert"], shown if len(shown) <= 14 else shown[:7] + [["…"] * 3] + shown[-6:]),
                              items=[("Anzahl", _fmt(res.count))], rule="Summenregel"))
        probe = (lambda w: bin(w).count("1") <= k)
    res.summary = f"{_fmt(res.count)} Bitwörter."
    if n <= 16:
        if sum(1 for w in range(2 ** n) if probe(w)) != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
    return res._finish()


def count_subsets(n: int | None = None, objects=None) -> CountResult:
    """
    Anzahl Teilmengen einer n-elementigen Menge A: |P(A)| = 2ⁿ (Serie 8, Aufgabe 6).
    Jede Teilmenge entspricht genau einem Bitwort der Länge n (Element drin = 1): bijektive Zuordnung.

    >>> count_subsets(2).count
    4
    >>> count_subsets(objects=["schwarz", "weiss"]).count
    4
    """
    if objects is not None:
        objs = list(objects)
        if len(set(objs)) != len(objs) or not 1 <= len(objs) <= 10:
            raise ValueError("objects: 1 bis 10 verschiedene Objekte")
        n = len(objs)
    n = _int(n, "n", 0, MAX_N)
    res = CountResult()
    res.count = 2 ** n
    res.formula = f"2^{n}"
    res.title = f"Potenzmenge einer Menge mit {n} Elementen"
    res.summary = f"|P(A)| = 2^{n} = {_fmt(res.count)}."
    res.steps.append(Step("Zuordnung", "Jeder Teilmenge T ⊆ A wird das Bitwort der Länge n zugeordnet, das an Stelle i eine 1 hat, wenn das i-te Element in T liegt. "
                          "Das ist eine Bijektion Teilmengen ↔ Bitwörter (k = 1).", rule="Zuordnungsregel"))
    res.steps.append(Step("Zählen", "Es gibt 2ⁿ Bitwörter der Länge n (Produktregel), also ebenso viele Teilmengen.",
                          items=[("|P(A)|", f"2^{n} = {_fmt(res.count)}")], rule="Produktregel"))
    if objects is not None:
        rows = []
        for w in itertools.product((0, 1), repeat=n):
            sub = "{" + ", ".join(str(o) for o, b in zip(objs, w) if b) + "}"
            rows.append(["".join(map(str, w)), sub if len(sub) > 2 else "{ }"])
        res.steps.append(Step("Probe durch Aufzählen", "Jedes Bitwort mit seiner Teilmenge.", table=Table(["Bitwort", "Teilmenge"], rows[:MAX_LIST])))
        res.items, res.checked = rows, len(rows) == res.count
    elif n <= 16:
        res.checked = sum(1 for _ in itertools.product((0, 1), repeat=n)) == res.count
    return res._finish("|P(A)|")


def count_surjections(n: int, m: int) -> CountResult:
    """
    n verschiedene Objekte auf m verschiedene Fächer verteilen, so dass kein Fach leer bleibt (Serie 8, Aufgabe 19 c).
    Siebformel: Σ_j (−1)ʲ·C(m, j)·(m−j)ⁿ. Das steht nicht in der Serie: TODO mit der Vorlesung abgleichen.

    >>> count_surjections(9, 3).count
    18150
    >>> count_surjections(4, 2).count
    14
    """
    n, m = _int(n, "n", 0, 400), _int(m, "m", 1, 200)
    res = CountResult()
    terms = [(-1) ** j * math.comb(m, j) * (m - j) ** n for j in range(m + 1)]
    res.count = sum(terms)
    res.formula = "Σ_(j=0..m) (−1)^j·C(m, j)·(m−j)^n"
    res.title = f"{n} verschiedene Objekte auf {m} Fächer, kein Fach leer"
    res.summary = f"{_fmt(res.count)} Möglichkeiten."
    res.steps.append(Step("Alle Verteilungen", f"Jedes der {n} Objekte kommt in eines von {m} Fächern: {m}^{n} Verteilungen (Variationen mit Wiederholungen).",
                          items=[("alle", _fmt(m ** n))], rule="Produktregel"))
    res.steps.append(Step("Leere Fächer abziehen",
                          "Verteilungen, bei denen mindestens j bestimmte Fächer leer bleiben, abwechselnd abziehen und wieder addieren (Siebformel).",
                          table=Table(["j", "Vorzeichen", "C(m, j)", "(m−j)^n", "Beitrag"],
                                      [[str(j), "+" if j % 2 == 0 else "−", str(math.comb(m, j)), _fmt((m - j) ** n), _fmt(t)] for j, t in enumerate(terms)]
                                      if m <= 14 else [[str(j), "+" if j % 2 == 0 else "−", "…", "…", _fmt(t)] for j, t in enumerate(terms[:6])]),
                          items=[("Anzahl", _fmt(res.count))], rule="Siebformel (nicht in der Serie)",
                          note="Gegenprobe: m = n gibt n!."))
    if m ** n <= MAX_BRUTE:
        got = sum(1 for f in itertools.product(range(m), repeat=n) if len(set(f)) == m)
        if got != res.count:
            raise AssertionError("Aufzählung weicht von der Formel ab")             # nie erwartet
        res.checked = True
    return res._finish()


def lattice_paths(right: int, up: int, via=None) -> CountResult:
    """
    Kürzeste Wege in einem Gitter von (0, 0) nach (right, up), nur nach rechts oder oben (Serie 8, Aufgabe 20).
    Jeder Weg ist ein Wort aus ``right`` mal R und ``up`` mal O: C(right+up, right). Mit ``via=(r, u)`` nur Wege über diesen Punkt
    (Produktregel: Weg bis dorthin mal Weg von dort).

    >>> lattice_paths(6, 4).count
    210
    >>> lattice_paths(6, 4, via=(2, 2)).count
    90
    """
    r, u = _int(right, "right", 0, MAX_N), _int(up, "up", 0, MAX_N)
    res = CountResult()
    if via is None:
        res.count = math.comb(r + u, r)
        res.formula = f"C({r + u}, {r})"
        res.title = f"Kürzeste Wege im Gitter: {r} nach rechts, {u} nach oben"
        res.steps.append(Step("Zuordnung", f"Ein kürzester Weg besteht aus {r} Schritten nach rechts (R) und {u} nach oben (O), in beliebiger Reihenfolge. "
                              f"Wege ↔ Wörter mit {r} R und {u} O ↔ Wahl der {r} Stellen für R (bijektiv).", rule="Zuordnungsregel"))
        res.steps.append(Step("Formel", "Kombinationen ohne Wiederholungen", items=[("Anzahl", f"{res.formula} = {_fmt(res.count)}")],
                              rule="Kombination ohne Wiederholungen"))
        parts = None
    else:
        if (not isinstance(via, (tuple, list)) or len(via) != 2):
            raise ValueError("via: ein Punkt (rechts, oben)")
        vr, vu = _int(via[0], "via[0]", 0, r), _int(via[1], "via[1]", 0, u)
        first, second = math.comb(vr + vu, vr), math.comb((r - vr) + (u - vu), r - vr)
        res.count = first * second
        res.formula = f"C({vr + vu}, {vr}) · C({r - vr + u - vu}, {r - vr})"
        res.title = f"Kürzeste Wege im Gitter über den Punkt ({vr}, {vu}): {r} nach rechts, {u} nach oben"
        res.steps.append(Step("Zerlegen", f"Ein Weg über ({vr}, {vu}) besteht aus einem Weg von (0, 0) dorthin und einem von dort nach ({r}, {u}); "
                              "beide Teile sind unabhängig.", rule="Produktregel"))
        res.steps.append(Step("Teilwege", "Je Teil Kombinationen ohne Wiederholungen.",
                              items=[("bis zum Punkt", f"C({vr + vu}, {vr}) = {first}"), ("danach", f"C({r - vr + u - vu}, {r - vr}) = {second}")],
                              rule="Kombination ohne Wiederholungen"))
        res.steps.append(Step("Produkt", "", items=[("Anzahl", f"{first} · {second} = {_fmt(res.count)}")], rule="Produktregel"))
    res.summary = f"{_fmt(res.count)} Wege."
    # Probe: Wege per Summe der Nachbarn zählen (dynamische Programmierung), ohne die Formel zu benutzen
    def dp_paths(w, h):
        g = [[1 if x == y == 0 else 0 for y in range(h + 1)] for x in range(w + 1)]
        for x in range(w + 1):
            for y in range(h + 1):
                if x or y:
                    g[x][y] = (g[x - 1][y] if x else 0) + (g[x][y - 1] if y else 0)
        return g[w][h]
    dp = dp_paths(r, u) if via is None else dp_paths(via[0], via[1]) * dp_paths(r - via[0], u - via[1])
    if dp != res.count:
        raise AssertionError("Weg-Zählung weicht von der Formel ab")                # nie erwartet
    res.checked = True
    return res._finish()


# ==========================================================================
# IPv4-Teilnetz (Aufgabe 22)
# ==========================================================================

class NetworkResult(Result):
    """``network`` (Netzname), ``broadcast``, ``first_host``, ``last_host``, ``hosts`` (Anzahl), ``prefix``, ``host_bits``."""


def _bits32(a: ipaddress.IPv4Address) -> str:
    b = format(int(a), "032b")
    return " ".join(b[i:i + 8] for i in range(0, 32, 8))


def ip_network(cidr: str) -> NetworkResult:
    """
    IPv4-Teilnetz in CIDR-Notation, etwa ``"191.0.13.143/26"`` (Serie 8, Aufgabe 22): Netzname (alle Hostbits 0), Broadcast
    (alle Hostbits 1) und die Hosts dazwischen. Anzahl Hosts: 2^(32 − Präfix) − 2.

    >>> ip_network("191.0.13.143/26").hosts
    62
    >>> ip_network("186.13.157.160/27").hosts
    30
    """
    if not isinstance(cidr, str) or "/" not in cidr or len(cidr) > 32:
        raise ValueError("Bitte im Format 191.0.13.143/26 angeben")
    try:
        net = ipaddress.IPv4Network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ValueError(f"Keine gültige IPv4-Adresse mit Präfix: {cidr!r} ({exc})") from None
    if net.prefixlen > 30:
        raise ValueError("Präfix von 0 bis 30: bei /31 und /32 gibt es keine Host-Adressen im Sinne der Serie (Netzname und Broadcast)")
    res = NetworkResult()
    p = net.prefixlen
    res.prefix, res.host_bits = p, 32 - p
    res.network, res.broadcast = str(net.network_address), str(net.broadcast_address)
    res.first_host, res.last_host = str(net.network_address + 1), str(net.broadcast_address - 1)
    res.hosts = 2 ** (32 - p) - 2
    if res.hosts != int(net.broadcast_address) - int(net.network_address) - 1:
        raise AssertionError("Hostzahl stimmt nicht")                                # nie erwartet
    res.title = f"IPv4-Teilnetz {cidr.strip()}"
    res.summary = f"Netz {res.network}/{p}, {res.hosts} Hosts: {res.first_host} bis {res.last_host}."
    given = ipaddress.IPv4Address(cidr.split("/")[0].strip())
    res.steps.append(Step("Aufteilen", f"Die ersten {p} Bits sind der Netzanteil, die letzten {32 - p} Bits der Hostanteil.",
                          items=[("Adresse", _bits32(given)), ("Netzanteil", f"{p} Bits"), ("Hostanteil", f"{32 - p} Bits")], rule="CIDR"))
    res.steps.append(Step("Netzname und Broadcast", "Netzname: alle Hostbits 0. Broadcast: alle Hostbits 1. Beide sind keine Host-Adressen.",
                          items=[("Netzname", f"{_bits32(net.network_address)} = {res.network}"),
                                 ("Broadcast", f"{_bits32(net.broadcast_address)} = {res.broadcast}")], rule="CIDR"))
    res.steps.append(Step("Anzahl Hosts", f"Hostanteil mit {32 - p} Bits: 2^{32 - p} Adressen (Produktregel), davon zwei abziehen.",
                          items=[("Hosts", f"2^{32 - p} − 2 = {_fmt(res.hosts)}"), ("Bereich", f"{res.first_host} – {res.last_host}")],
                          rule="Produktregel"))
    res.highlights = [("Hosts", res.hosts)]
    return res
