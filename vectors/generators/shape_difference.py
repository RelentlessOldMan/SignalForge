"""Writes vectors/cases/shape_difference.json, stdlib only.

The shape difference (conventions: the shape difference; ADR 0473): the 2x2 table counted
directly, the value formed in rationals.

Run from the repo root: python vectors/generators/shape_difference.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    q = Fr(len(t) * (fn + fp) - (fn - fp) ** 2, len(t) ** 2)
    cases.append(
        {
            "id": f"shape_difference.{cid}",
            "op": "shape_difference",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "FN 0, FP 0: 0, the least value")
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2, n 4: (16 - 0)/16 = 1, the greatest value",
)
assert got == 1
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: (8 - 0)/16 = 1/2"
)
assert got == Fr(1, 2)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "FN 1, FP 1, n 10: 20/100 = 1/5",
)
assert got == Fr(1, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "FN 1, FP 0, n 6: (6 - 1)/36 = 5/36",
)
assert got == Fr(5, 36)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "FN 1, FP 3, n 7: (28 - 4)/49 = 24/49",
)
assert got == Fr(24, 49)
got = add(
    "one_way",
    [0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0],
    "FP 3, n 3: (9 - 9)/9 = 0, opposite but all one way",
)
assert got == 0
rng = random.Random(473)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(473), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"shape_difference.{cid}",
            "op": "shape_difference",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])

doc = {
    "schema": 1,
    "suite": "shape_difference",
    "description": "The shape difference (conventions: the shape difference; ADR 0473).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "shape_difference.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/shape_difference.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
