"""Writes vectors/cases/scott_pi.json, stdlib only.

Scott's pi (conventions: Scott's pi; ADR 0384): agreements and pooled counts in integers.

Run from the repo root: python vectors/generators/scott_pi.py [--check]
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
    pooled = sum((a.count(c) + b.count(c)) ** 2 for c in set(a) | set(b))
    pi = Fr(4 * n * agree - pooled, 4 * n * n - pooled)
    cases.append({"id": f"scott_pi.{cid}", "op": "scott_pi", "args": {"a": a, "b": b},
                  "expected": float(pi), "tol": TOL, "source": why})
    return agree, pooled, pi


# The 2 x 2 table of the Cohen's kappa vectors: yes/yes 20, yes/no 5, no/yes 10, no/no 15.
a = [1.0] * 25 + [0.0] * 25
b = [1.0] * 20 + [0.0] * 5 + [1.0] * 10 + [0.0] * 15
got = add("two_by_two", a, b,
          "yes is used 25 + 30 = 55 times of 100, no 45: p_e = 0.55^2 + 0.45^2 = 0.505; "
          "p_o = 0.7; pi = 0.195/0.495 = 13/33 (Cohen's kappa is 0.4)")
assert got == (35, 5050, Fr(13, 33))
got = add("full_agreement", [0.0, 1.0, 2.0, 1.0], [0.0, 1.0, 2.0, 1.0],
          "identical labels: 4NA = 64, F = 4 + 16 + 4 = 24, pi = 40/40 = 1")
assert got == (4, 24, 1)
got = add("none_agree", [0.0, 1.0], [1.0, 0.0],
          "two labels swapped: A = 0, F = 4 + 4 = 8, pi = -8/8 = -1")
assert got == (0, 8, -1)
got = add("unshared_category", [0.0, 0.0, 1.0, 2.0], [0.0, 1.0, 1.0, 1.0],
          "pooled counts 3, 4, 1: F = 26; A = 2; pi = (32 - 26)/(64 - 26) = 3/19")
assert got == (2, 26, Fr(3, 19))
rng = random.Random(384)
a = [float(rng.randint(0, 4)) for _ in range(60)]
b = [v if rng.random() < 0.6 else float(rng.randint(0, 2)) for v in a]
add("five_classes", a, b, "60 labels in 0..4 from random.Random(384); b copies a with "
    "probability 0.6, else a random label in 0..2, so the rates differ")


def err(cid, why, **args):
    base = {"a": [0.0, 1.0, 1.0, 2.0], "b": [0.0, 1.0, 2.0, 2.0]}
    base.update(args)
    cases.append({"id": f"scott_pi.{cid}", "op": "scott_pi", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "a and b must be the same length", b=[0.0, 1.0, 2.0])
err("empty", "N must be at least 1", a=[], b=[])
err("one_label", "p_e = 1 when every label is the same", a=[3.0, 3.0, 3.0], b=[3.0, 3.0, 3.0])
err("nan", "labels must be finite", b=[0.0, "nan", 2.0, 2.0])

doc = {
    "schema": 1,
    "suite": "scott_pi",
    "description": "Scott's pi (conventions: Scott's pi; ADR 0384).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "scott_pi.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/scott_pi.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
