"""Writes vectors/cases/relative_risk.json, stdlib only.

The relative risk (conventions: the relative risk; ADR 0484): the 2x2 table counted
directly, the value formed in rationals.

Run from the repo root: python vectors/generators/relative_risk.py [--check]
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
    q = Fr(tp * (fn + tn), (tp + fp) * fn)
    cases.append(
        {
            "id": f"relative_risk.{cid}",
            "op": "relative_risk",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 1 2/(2 1) = 1"
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "TP 0, FP 2, FN 2, TN 0: 0/4 = 0, the least value",
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: 4 5/(5 1) = 4",
)
assert got == 4
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: 2 2/(5 1) = 4/5",
)
assert got == Fr(4, 5)
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 3, FN 1, FP 1, TN 2: 3 3/(4 1) = 9/4",
)
assert got == Fr(9, 4)
got = add(
    "truth_all_one", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "TP 2, FN 1, FP 0, TN 0: 2 1/(2 1) = 1"
)
assert got == 1
rng = random.Random(484)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(484), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"relative_risk.{cid}",
            "op": "relative_risk",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "no_decision_one",
    "the decision has no 1: TP + FP = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[0.0, 0.0, 0.0],
)
err("no_fn", "equal records: FN = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[1.0, 0.0, 1.0, 0.0])
err(
    "decision_all_one",
    "the decision has no 0: FN = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "relative_risk",
    "description": "The relative risk (conventions: the relative risk; ADR 0484).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "relative_risk.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/relative_risk.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
