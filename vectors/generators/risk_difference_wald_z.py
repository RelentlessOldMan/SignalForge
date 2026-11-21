"""Writes vectors/cases/risk_difference_wald_z.json, stdlib only.

The Wald z of the risk difference (conventions: the Wald z of the risk difference;
ADR 0503): the 2x2 table counted directly, the risk difference and its squared standard
error in rationals, the square root in 40-digit decimals.

Run from the repo root: python vectors/generators/risk_difference_wald_z.py [--check]
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

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    rd = Fr(tp, tp + fp) - Fr(fn, fn + tn)
    f = Fr(tp * fp, (tp + fp) ** 3) + Fr(fn * tn, (fn + tn) ** 3)
    q = D(rd.numerator) / D(rd.denominator) / (D(f.numerator) / D(f.denominator)).sqrt()
    cases.append(
        {
            "id": f"risk_difference_wald_z.{cid}",
            "op": "risk_difference_wald_z",
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
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: risk difference 0"
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: (3/5)/(2 sqrt 10/25) = 3 sqrt 10/4",
)
assert close(got, 3 * D(10).sqrt() / 4)
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 1, TN 2: (1/3)/(2/(3 sqrt 3)) = sqrt 3/2",
)
assert close(got, D(3).sqrt() / 2)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: (-1/10)/sqrt(173/1000) = -sqrt(10/173)",
)
assert close(got, -(D(10) / 173).sqrt())
got = add(
    "one_term",
    [1.0, 1.0, 1.0, 0.0],
    [1.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 0, TN 1: (1 - 1/2)/sqrt(0 + 1/8) = sqrt 2",
)
assert close(got, D(2).sqrt())
rng = random.Random(503)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(503), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"risk_difference_wald_z.{cid}",
            "op": "risk_difference_wald_z",
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
err(
    "no_spread",
    "equal records: TP FP = FN TN = 0, the standard error is 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 0.0, 1.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "risk_difference_wald_z",
    "description": "The Wald z of the risk difference (conventions: the Wald z of the risk"
    " difference; ADR 0503).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "risk_difference_wald_z.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/risk_difference_wald_z.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
