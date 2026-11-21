"""Writes vectors/cases/relative_risk_reduction.json, stdlib only.

The relative risk reduction (conventions: the relative risk reduction; ADR 0505): the
2x2 table counted directly, (FN FP - TP TN) / ((TP + FP) FN) in 40-digit decimals.

Run from the repo root: python vectors/generators/relative_risk_reduction.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    q = D(fn * fp - tp * tn) / D((tp + fp) * fn)
    cases.append(
        {
            "id": f"relative_risk_reduction.{cid}",
            "op": "relative_risk_reduction",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: (1 - 1)/(2 1) = 0"
)
assert got == 0
got = add(
    "no_exposed_case", [0.0, 0.0, 1.0, 1.0], [1.0, 1.0, 0.0, 0.0], "FN 2, FP 2: (4 - 0)/(2 2) = 1"
)
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: (1 - 16)/(5 1) = -3",
)
assert got == -3
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 1, TN 2: (1 - 4)/(3 1) = -1",
)
assert got == -1
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: (3 - 2)/(5 1) = 1/5",
)
assert close(got, D(1) / 5)
rng = random.Random(505)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(505), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"relative_risk_reduction.{cid}",
            "op": "relative_risk_reduction",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "decision_all_one",
    "the decision has no 0, so FN = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)
err("decision_all_zero", "the decision has no 1", truth=[1.0, 0.0, 1.0], decision=[0.0, 0.0, 0.0])
err(
    "no_false_negative",
    "equal records: FN = 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 0.0, 1.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "relative_risk_reduction",
    "description": "The relative risk reduction (conventions: the relative risk reduction;"
    " ADR 0505).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "relative_risk_reduction.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/relative_risk_reduction.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
