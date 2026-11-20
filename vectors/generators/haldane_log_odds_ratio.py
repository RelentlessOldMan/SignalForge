"""Writes vectors/cases/haldane_log_odds_ratio.json, stdlib only.

The Haldane log odds ratio (conventions: the Haldane log odds ratio; ADR 0494): the 2x2
table counted directly, the logarithm of (2 TP + 1)(2 TN + 1) / ((2 FN + 1)(2 FP + 1)) in
40-digit decimals.

Run from the repo root: python vectors/generators/haldane_log_odds_ratio.py [--check]
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
    q = (D((2 * tp + 1) * (2 * tn + 1)) / D((2 * fn + 1) * (2 * fp + 1))).ln()
    cases.append(
        {
            "id": f"haldane_log_odds_ratio.{cid}",
            "op": "haldane_log_odds_ratio",
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
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: ln(9/9) = 0"
)
assert got == 0
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "TP 2, TN 2, FN = FP = 0: ln(5 5/(1 1)) = ln 25",
)
assert close(got, D(25).ln())
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2, TP = TN = 0: ln(1/25) = -ln 25",
)
assert close(got, -D(25).ln())
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: ln(9 9/(3 3)) = ln 9",
)
assert close(got, D(9).ln())
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: ln(5 3/(3 7)) = ln(5/7)",
)
assert close(got, (D(5) / 7).ln())
got = add("single", [1.0], [1.0], "TP 1 only: ln(3 1/(1 1)) = ln 3")
assert close(got, D(3).ln())
rng = random.Random(494)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(494), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"haldane_log_odds_ratio.{cid}",
            "op": "haldane_log_odds_ratio",
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
    "suite": "haldane_log_odds_ratio",
    "description": "The Haldane log odds ratio (conventions: the Haldane log odds ratio;"
    " ADR 0494).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "haldane_log_odds_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/haldane_log_odds_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
