"""Writes vectors/cases/size_difference.json, stdlib only.

The size difference (conventions: the size difference; ADR 0472): the 2x2 table counted
directly, the value formed in rationals.

Run from the repo root: python vectors/generators/size_difference.py [--check]
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
    q = Fr((fn + fp) ** 2, len(t) ** 2)
    cases.append(
        {
            "id": f"size_difference.{cid}",
            "op": "size_difference",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "FN + FP 0: 0, the least value")
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN + FP 4, n 4: 16/16 = 1, the greatest value",
)
assert got == 1
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 4/16 = 1/4")
assert got == Fr(1, 4)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "FN 1, FP 1, n 10: 4/100 = 1/25",
)
assert got == Fr(1, 25)
got = add(
    "subset", [1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0, 0.0], "FN 1, n 6: 1/36"
)
assert got == Fr(1, 36)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "FN 1, FP 3, n 7: 16/49",
)
assert got == Fr(16, 49)
got = add("all_one", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], "both all 1: 0, no error")
assert got == 0
rng = random.Random(472)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(472), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"size_difference.{cid}",
            "op": "size_difference",
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
    "suite": "size_difference",
    "description": "The size difference (conventions: the size difference; ADR 0472).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "size_difference.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/size_difference.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
