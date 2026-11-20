"""Writes vectors/cases/johnson_coefficient.json, stdlib only.

The Johnson coefficient (conventions: the Johnson coefficient; ADR 0470): the 2x2 table
counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/johnson_coefficient.py [--check]
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
    q = Fr(tp, tp + fn) + Fr(tp, tp + fp)
    cases.append(
        {
            "id": f"johnson_coefficient.{cid}",
            "op": "johnson_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, |A| 2, |B| 2: 1 + 1 = 2")
assert got == 2
got = add("disjoint", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "TP 0: 0, the least value")
assert got == 0
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 1, |A| 2, |B| 2: 1/2 + 1/2 = 1"
)
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, |A| 5, |B| 5: 8/5",
)
assert got == Fr(8, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, |A| 3, |B| 2: 2/3 + 1 = 5/3",
)
assert got == Fr(5, 3)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, |A| 3, |B| 5: 2/3 + 2/5 = 16/15",
)
assert got == Fr(16, 15)
got = add("all_one", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], "both all 1: 1 + 1 = 2, no error")
assert got == 2
rng = random.Random(470)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(470), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"johnson_coefficient.{cid}",
            "op": "johnson_coefficient",
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
    "suite": "johnson_coefficient",
    "description": "The Johnson coefficient (conventions: the Johnson coefficient; ADR 0470).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "johnson_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/johnson_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
