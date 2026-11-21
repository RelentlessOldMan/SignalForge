"""Writes vectors/cases/risk_difference.json, stdlib only.

The risk difference (conventions: the risk difference; ADR 0501): the 2x2 table counted
directly, TP/(TP + FP) - FN/(FN + TN) in rationals, then divided in 40-digit decimals.

Run from the repo root: python vectors/generators/risk_difference.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as Fr

getcontext().prec = 40

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    f = Fr(tp, tp + fp) - Fr(fn, fn + tn)
    q = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"risk_difference.{cid}",
            "op": "risk_difference",
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
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 1/2 - 1/2 = 0"
)
assert got == 0
got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, TN 2: 2/2 - 0/2 = 1")
assert got == 1
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2: 0/2 - 2/2 = -1")
assert got == -1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: 4/5 - 1/5 = 3/5",
)
assert close(got, D(3) / 5)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: 2/5 - 1/2 = -1/10",
)
assert close(got, D(-1) / 10)
got = add("all_truth_one", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "TP 2, FN 1: 2/2 - 1/1 = 0")
assert got == 0
rng = random.Random(501)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(501), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"risk_difference.{cid}",
            "op": "risk_difference",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("decision_all_one", "the decision has no 0", truth=[1.0, 0.0, 1.0], decision=[1.0, 1.0, 1.0])
err("decision_all_zero", "the decision has no 1", truth=[1.0, 0.0, 1.0], decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "risk_difference",
    "description": "The risk difference (conventions: the risk difference; ADR 0501).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "risk_difference.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/risk_difference.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
