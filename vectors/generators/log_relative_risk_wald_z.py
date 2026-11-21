"""Writes vectors/cases/log_relative_risk_wald_z.json, stdlib only.

The Wald z of the log relative risk (conventions: the Wald z of the log relative risk;
ADR 0500): the 2x2 table counted directly, ln(P/Q) sqrt(PQ/M) with the logarithm and the
square root in 40-digit decimals.

Run from the repo root: python vectors/generators/log_relative_risk_wald_z.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    pp, qq = tp * (fn + tn), fn * (tp + fp)
    m = fp * fn * (fn + tn) + tn * tp * (tp + fp)
    q = (D(pp) / D(qq)).ln() * (D(pp * qq) / D(m)).sqrt()
    cases.append(
        {
            "id": f"log_relative_risk_wald_z.{cid}",
            "op": "log_relative_risk_wald_z",
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
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: P = Q = 2, ln 1 = 0",
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: P 20, Q 5, M 85: ln 4 sqrt(20/17)",
)
assert close(got, D(4).ln() * (D(20) / 17).sqrt())
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 1, TN 2: P 6, Q 3, M 15: ln 2 sqrt(6/5)",
)
assert close(got, D(2).ln() * (D(6) / 5).sqrt())
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: P 4, Q 5, M 16: ln(4/5) sqrt(5/4)",
)
assert close(got, (D(4) / 5).ln() * (D(5) / 4).sqrt())
got = add(
    "mostly_caught",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0],
    "TP 3, FN 1, FP 1, TN 1: P 6, Q 4, M 14: ln(3/2) sqrt(12/7)",
)
assert close(got, (D(3) / 2).ln() * (D(12) / 7).sqrt())
rng = random.Random(500)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(500), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"log_relative_risk_wald_z.{cid}",
            "op": "log_relative_risk_wald_z",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_tp", "opposite records: TP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err(
    "no_fn",
    "every truth 1 caught: FN = 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 1.0, 1.0, 0.0],
)
err(
    "all_truth_one",
    "FP = TN = 0: the standard error is 0",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 0.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "log_relative_risk_wald_z",
    "description": "The Wald z of the log relative risk (conventions: the Wald z of the log"
    " relative risk; ADR 0500).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "log_relative_risk_wald_z.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/log_relative_risk_wald_z.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
