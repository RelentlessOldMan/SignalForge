"""Writes vectors/cases/cole_coefficient.json, stdlib only.

Cole's coefficient (conventions: Cole's coefficient; ADR 0445): the 2x2 table counted
directly, the covariance c = TP/n - pA pB formed in rationals and divided by
min(pA, pB) - pA pB when c >= 0, else by pA pB - max(0, pA + pB - 1).

Run from the repo root: python vectors/generators/cole_coefficient.py [--check]
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
    pa, pb = Fr(tp + fn, len(t)), Fr(tp + fp, len(t))
    c = Fr(tp, len(t)) - pa * pb
    q = c / (min(pa, pb) - pa * pb) if c >= 0 else c / (pa * pb - max(0, pa + pb - 1))
    cases.append(
        {
            "id": f"cole_coefficient.{cid}",
            "op": "cole_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, |A| = |B| = TP = 2: (1/2 - 1/4)/(1/2 - 1/4) = 1",
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, |A| = |B| = 2, TP 0: (0 - 1/4)/(1/4 - 0) = -1",
)
assert got == -1
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: TP/n = pA pB = 1/4, 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, |A| = |B| = 2, TP 1: (1/5 - 4/25)/(2/5 - 4/25) = 1/6",
)
assert got == Fr(1, 6)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, |A| = |B| = 5, TP 4: (2/5 - 1/4)/(1/2 - 1/4) = 3/5",
)
assert got == Fr(3, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "B inside A, n 5, |A| 3, |B| 1, TP 1: (1/5 - 3/25)/(1/5 - 3/25) = 1",
)
assert got == 1
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, |A| 1, |B| 3, TP 0: (0 - 3/16)/(3/16 - 0) = -1, the least TP these counts allow",
)
assert got == -1
got = add(
    "negative",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    "n 6, |A| = |B| = 3, TP 1: (1/6 - 1/4)/(1/4 - 0) = -1/3",
)
assert got == Fr(-1, 3)
got = add(
    "negative_crowded",
    [1.0, 1.0, 1.0, 1.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 1.0],
    "n 5, |A| 4, |B| 3, TP 2: (2/5 - 12/25)/(12/25 - 2/5) = -1, TP at its least of 2",
)
assert got == -1
rng = random.Random(445)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(445), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cole_coefficient.{cid}",
            "op": "cole_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("all_one", "truth all 1: both bounds are 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])
err("all_zero", "decision all 0: both bounds are 0", decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "cole_coefficient",
    "description": "Cole's coefficient (conventions: Cole's coefficient; ADR 0445).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cole_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cole_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
