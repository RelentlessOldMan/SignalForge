"""Writes vectors/cases/ruzicka_similarity.json, stdlib only.

The Ruzicka similarity of two records (conventions: Ruzicka similarity of two records;
ADR 0580): sum(min)/sum(max) with fractions.

Run from the repo root: python vectors/generators/ruzicka_similarity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 60
TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    f = Fr(sum(min(a, b) for a, b in zip(xs, ys)), sum(max(a, b) for a, b in zip(xs, ys)))
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"ruzicka_similarity.{cid}",
            "op": "ruzicka_similarity",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("same", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "identical records: 1") == 1
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "no shared kind: 0") == 0
assert add("double", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "a record and its double: 6/12") == D(1) / 2
assert (
    add("crossed", [1.0, 2.0, 0.0, 4.0], [0.0, 3.0, 5.0, 1.0], "min 0+2+0+1, max 1+3+5+4: 3/13")
    == D(3) / 13
)
assert add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "presence records: Jaccard 1/3") == D(1) / 3
assert (
    add("huge", [1.5e308, 1.5e308], [1.5e308, 0.0], "sums past the largest double: 1/2") == D(1) / 2
)
assert (
    add("tiny", [5e-324, 0.0], [1e-323, 0.0], "subnormal values: 5e-324/1e-323 = 1/2") == D(1) / 2
)
assert (
    add(
        "uneven",
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "presence records, a = 1, b = 4, c = 1: 1/6",
    )
    == D(1) / 6
)
rng = random.Random(580)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(580).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"ruzicka_similarity.{cid}",
            "op": "ruzicka_similarity",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], y=[])
err("negative", "values must be at least 0", y=[1.0, -0.5, 2.0])
err("all_zero", "each record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", y=[1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "ruzicka_similarity",
    "description": "The Ruzicka similarity of two records (conventions: Ruzicka similarity of two records; ADR 0580).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ruzicka_similarity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ruzicka_similarity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
