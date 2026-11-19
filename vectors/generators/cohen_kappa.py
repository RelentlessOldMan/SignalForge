"""Writes vectors/cases/cohen_kappa.json, stdlib only.

Cohen's kappa (conventions: Cohen's kappa; ADR 0383): agreements and chance products counted
in integers.

Run from the repo root: python vectors/generators/cohen_kappa.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, a, b, why):
    n = len(a)
    agree = sum(1 for u, v in zip(a, b) if u == v)
    chance = sum(a.count(c) * b.count(c) for c in set(a) | set(b))
    kappa = Fr(n * agree - chance, n * n - chance)
    cases.append({"id": f"cohen_kappa.{cid}", "op": "cohen_kappa", "args": {"a": a, "b": b},
                  "expected": float(kappa), "tol": TOL, "source": why})
    return agree, chance, kappa


# The textbook 2 x 2 table: yes/yes 20, yes/no 5, no/yes 10, no/no 15.
a = [1.0] * 25 + [0.0] * 25
b = [1.0] * 20 + [0.0] * 5 + [1.0] * 10 + [0.0] * 15
got = add("two_by_two", a, b,
          "50 items: both yes 20, yes/no 5, no/yes 10, both no 15; p_o = 35/50 = 0.7, "
          "p_e = (25*30 + 25*20)/2500 = 0.5, kappa = 0.2/0.5 = 0.4")
assert got == (35, 1250, Fr(2, 5))
got = add("full_agreement", [0.0, 1.0, 2.0, 1.0], [0.0, 1.0, 2.0, 1.0],
          "identical labels: NA = 16, E = 1 + 4 + 1 = 6, kappa = 10/10 = 1")
assert got == (4, 6, 1)
got = add("none_agree", [0.0, 1.0], [1.0, 0.0],
          "the raters swap two labels: A = 0, E = 2, kappa = -2/2 = -1")
assert got == (0, 2, -1)
got = add("unshared_category", [0.0, 0.0, 1.0, 2.0], [0.0, 1.0, 1.0, 1.0],
          "2 appears only in a: A = 2, E = 2*1 + 1*3 = 5, kappa = (8 - 5)/(16 - 5) = 3/11")
assert got == (2, 5, Fr(3, 11))
rng = random.Random(383)
a = [float(rng.randint(0, 4)) for _ in range(60)]
b = [v if rng.random() < 0.6 else float(rng.randint(0, 4)) for v in a]
add("five_classes", a, b, "60 labels in 0..4 from random.Random(383); b copies a with "
    "probability 0.6, else a random label")


def err(cid, why, **args):
    base = {"a": [0.0, 1.0, 1.0, 2.0], "b": [0.0, 1.0, 2.0, 2.0]}
    base.update(args)
    cases.append({"id": f"cohen_kappa.{cid}", "op": "cohen_kappa", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "a and b must be the same length", b=[0.0, 1.0, 2.0])
err("empty", "N must be at least 1", a=[], b=[])
err("one_label", "p_e = 1 when both raters use the same single label",
    a=[3.0, 3.0, 3.0], b=[3.0, 3.0, 3.0])
err("nan", "labels must be finite", b=[0.0, "nan", 2.0, 2.0])

doc = {
    "schema": 1,
    "suite": "cohen_kappa",
    "description": "Cohen's kappa (conventions: Cohen's kappa; ADR 0383).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cohen_kappa.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cohen_kappa.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
