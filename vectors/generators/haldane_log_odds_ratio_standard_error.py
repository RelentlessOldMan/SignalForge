"""Writes vectors/cases/haldane_log_odds_ratio_standard_error.json, stdlib only.

The standard error of the Haldane log odds ratio (conventions: the standard error of the
Haldane log odds ratio; ADR 0497): the 2x2 table counted directly, the reciprocals of the
cells plus a half summed in rationals and the square root taken in 40-digit decimals.

Run from the repo root: python vectors/generators/haldane_log_odds_ratio_standard_error.py [--check]
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
    f = Fr(2, 2 * tp + 1) + Fr(2, 2 * fn + 1) + Fr(2, 2 * fp + 1) + Fr(2, 2 * tn + 1)
    q = (D(f.numerator) / D(f.denominator)).sqrt()
    cases.append(
        {
            "id": f"haldane_log_odds_ratio_standard_error.{cid}",
            "op": "haldane_log_odds_ratio_standard_error",
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
    "one of each cell: 4 (2/3) = 8/3, sqrt(8/3)",
)
assert close(got, (D(8) / 3).sqrt())
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "TP 2, TN 2, FN = FP = 0: 2/5 + 2/5 + 2 + 2 = 24/5, sqrt(24/5)",
)
assert close(got, (D(24) / 5).sqrt())
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: 2/9 + 2/3 + 2/3 + 2/9 = 16/9, sqrt = 4/3",
)
assert close(got, D(4) / 3)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: 2/5 + 2/3 + 2/7 + 2/3 = 212/105, sqrt(212/105)",
)
assert close(got, (D(212) / 105).sqrt())
got = add("single", [1.0], [1.0], "TP 1 only: 2/3 + 2 + 2 + 2 = 20/3, sqrt(20/3)")
assert close(got, (D(20) / 3).sqrt())
rng = random.Random(497)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(497), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"haldane_log_odds_ratio_standard_error.{cid}",
            "op": "haldane_log_odds_ratio_standard_error",
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
    "suite": "haldane_log_odds_ratio_standard_error",
    "description": "The standard error of the Haldane log odds ratio (conventions: the"
    " standard error of the Haldane log odds ratio; ADR 0497).",
    "cases": cases,
}
out = (
    pathlib.Path(__file__).resolve().parents[1]
    / "cases"
    / "haldane_log_odds_ratio_standard_error.json"
)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/haldane_log_odds_ratio_standard_error.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
