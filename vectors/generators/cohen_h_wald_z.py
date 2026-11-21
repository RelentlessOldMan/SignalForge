"""Writes vectors/cases/cohen_h_wald_z.json, stdlib only.

The Wald z of Cohen's h (conventions: the Wald z of Cohen's h; ADR 0508): the 2x2 table
counted directly, then 2 (atan(sqrt(TP/FP)) - atan(sqrt(FN/TN))) in 50-digit decimals,
the arctangent by argument halving and the Taylor series, pi taken as a 50-digit
constant, divided by sqrt(N / ((TP + FP)(FN + TN))).

Run from the repo root: python vectors/generators/cohen_h_wald_z.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
PI = D("3.14159265358979323846264338327950288419716939937510")

TOL = {"abs": 1e-14, "rel": 1e-14}


def atan(x):
    if x > 1:
        return PI / 2 - atan(1 / x)
    k = 0
    while x > D("0.05"):
        x = x / (1 + (1 + x * x).sqrt())
        k += 1
    total, term, n = D(0), x, 0
    while abs(term) > D(10) ** -55:
        total += term / (2 * n + 1) * (-1 if n % 2 else 1)
        term *= x * x
        n += 1
    return total * 2**k


def half_angle(a, b):
    return PI / 2 if b == 0 else atan((D(a) / D(b)).sqrt())


cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    se = (D(len(t)) / D((tp + fp) * (fn + tn))).sqrt()
    q = 2 * (half_angle(tp, fp) - half_angle(fn, tn)) / se
    cases.append(
        {
            "id": f"cohen_h_wald_z.{cid}",
            "op": "cohen_h_wald_z",
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
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: equal shares, 0"
)
assert close(got, 0)
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "TP 2, TN 2: h = pi, standard error sqrt(4/4) = 1",
)
assert close(got, PI)
got = add(
    "opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2: h = -pi, standard error 1"
)
assert close(got, -PI)
got = add(
    "quarter",
    [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
    "TP 1, FP 3, FN 1, TN 1: h = -pi/6, standard error sqrt(6/8) = sqrt 3/2, so -pi/(3 sqrt 3)",
)
assert close(got, -PI / (3 * D(3).sqrt()))
got = add(
    "three_quarters",
    [1.0] * 3 + [0.0] + [1.0] + [0.0] * 3,
    [1.0] * 4 + [0.0] * 4,
    "TP 3, FP 1, FN 1, TN 3: h = pi/3, standard error sqrt(8/16), so pi sqrt 2/3",
)
assert close(got, PI * D(2).sqrt() / 3)
got = add("all_truth_one", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "TP 2, FN 1: h = 0")
assert close(got, 0)
rng = random.Random(508)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(508), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cohen_h_wald_z.{cid}",
            "op": "cohen_h_wald_z",
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
    "suite": "cohen_h_wald_z",
    "description": "The Wald z of Cohen's h (conventions: the Wald z of Cohen's h; ADR 0508).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cohen_h_wald_z.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cohen_h_wald_z.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
