"""Writes vectors/cases/routledge_overlap_beta.json, stdlib only.

Routledge's overlap beta (conventions: Routledge's overlap beta; ADR 0597): the pooled
kinds S, the pairs of distinct pooled kinds r whose occurrences overlap (both kinds present
in some record), counted pair by pair, and S^2/(2r + S) - 1 with fractions.

Run from the repo root: python vectors/generators/routledge_overlap_beta.py [--check]
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
TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    both = sum(1 for a, b in zip(xs, ys) if a > 0 and b > 0)
    only_x = sum(1 for a, b in zip(xs, ys) if a > 0 and b == 0)
    only_y = sum(1 for a, b in zip(xs, ys) if a == 0 and b > 0)
    kinds = [(a > 0, b > 0) for a, b in zip(xs, ys) if a > 0 or b > 0]
    pooled = len(kinds)
    overlap = sum(
        1
        for i in range(pooled)
        for j in range(i + 1, pooled)
        if (kinds[i][0] and kinds[j][0]) or (kinds[i][1] and kinds[j][1])
    )
    f = Fr(pooled * pooled, 2 * overlap + pooled) - 1
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"routledge_overlap_beta.{cid}",
            "op": "routledge_overlap_beta",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert add("same", [1.0, 2.0, 3.0], [5.0, 0.5, 1.0], "the same kinds: S = 3, r = 3: 0") == 0
assert add("disjoint", [1.0, 0.0], [0.0, 1.0], "S = 2, r = 0: 4/2 - 1 = 1") == 1
assert add("subset", [1.0, 1.0], [1.0, 0.0], "S = 2, r = 1: 4/4 - 1 = 0") == 0
assert (
    add("crossed", [1.0, 2.0, 0.0, 4.0], [0.0, 3.0, 5.0, 1.0], "S = 4, r = 5: 16/14 - 1 = 1/7")
    == D(1) / 7
)
assert add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "S = 3, r = 3: 0") == 0
assert (
    add(
        "swap",
        [1.0, 1.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 1.0, 1.0],
        "S = 5, r = 6: 25/17 - 1 = 8/17",
    )
    == D(8) / 17
)
assert (
    add(
        "uneven",
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "S = 6, r = 11: 36/28 - 1 = 2/7",
    )
    == D(2) / 7
)
assert (
    add(
        "lopsided",
        [1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 1.0, 1.0, 1.0],
        "S = 5, r = 6: 25/17 - 1 = 8/17",
    )
    == D(8) / 17
)
assert (
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [0.0, 1e-300, 1.0],
        "the smallest double counts as present: S = 3, r = 2: 9/7 - 1 = 2/7",
    )
    == D(2) / 7
)
rng = random.Random(597)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(597).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"routledge_overlap_beta.{cid}",
            "op": "routledge_overlap_beta",
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
    "suite": "routledge_overlap_beta",
    "description": "Routledge's overlap beta of two presence records (conventions: Routledge's overlap beta; ADR 0597).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "routledge_overlap_beta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/routledge_overlap_beta.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
