"""Writes vectors/cases/fossum_coefficient.json, stdlib only.

Fossum's coefficient (conventions: Fossum's coefficient; ADR 0449): the 2x2 table counted
directly, the value formed in rationals as n (TP - 1/2)^2 / (|A| |B|).

Run from the repo root: python vectors/generators/fossum_coefficient.py [--check]
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
    q = len(t) * (tp - Fr(1, 2)) ** 2 / ((tp + fn) * (tp + fp))
    cases.append(
        {
            "id": f"fossum_coefficient.{cid}",
            "op": "fossum_coefficient",
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
    "n 4, TP 2, |A| = |B| = 2: 4 (3/2)^2/4 = 9/4",
)
assert got == Fr(9, 4)
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, TP 0, |A| = |B| = 2: 4 (1/2)^2/4 = 1/4",
)
assert got == Fr(1, 4)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 1, |A| = |B| = 2: 4 (1/2)^2/4 = 1/4",
)
assert got == Fr(1, 4)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, TP 1, |A| = |B| = 2: 5 (1/2)^2/4 = 5/16",
)
assert got == Fr(5, 16)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, |A| = |B| = 5: 10 (7/2)^2/25 = 49/10",
)
assert got == Fr(49, 10)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2, |A| 3, |B| 2: 6 (3/2)^2/6 = 9/4",
)
assert got == Fr(9, 4)
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, TP 0, |A| 1, |B| 3: 4 (1/2)^2/3 = 1/3",
)
assert got == Fr(1, 3)
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1, n 3, TP 2, |B| 2: 3 (3/2)^2/6 = 9/8, no error",
)
assert got == Fr(9, 8)
rng = random.Random(449)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(449), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"fossum_coefficient.{cid}",
            "op": "fossum_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_decision_one", "decision all 0: |B| = 0", decision=[0.0, 0.0, 0.0])
err("no_truth_one", "truth all 0: |A| = 0", truth=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "fossum_coefficient",
    "description": "Fossum's coefficient (conventions: Fossum's coefficient; ADR 0449).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fossum_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fossum_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
