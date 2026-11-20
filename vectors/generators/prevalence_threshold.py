"""Writes vectors/cases/prevalence_threshold.json, stdlib only.

The prevalence threshold (conventions: the prevalence threshold; ADR 0487): the 2x2 table
counted directly, (sqrt(TP FP a b) - FP a) / (TP b - FP a) with the square root correctly
rounded in 40-digit decimals.

Run from the repo root: python vectors/generators/prevalence_threshold.py [--check]
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
    a, b = tp + fn, len(t) - tp - fn
    q = (D(tp * fp * a * b).sqrt() - fp * a) / D(tp * b - fp * a)
    cases.append(
        {
            "id": f"prevalence_threshold.{cid}",
            "op": "prevalence_threshold",
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
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FP 1, a 5, b 5: (sqrt 100 - 5)/(20 - 5) = 1/3",
)
assert close(got, D(1) / 3)
got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "FP 0: 0/4 = 0, the least value")
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "TP 0, FP 2, a 2, b 2: (0 - 4)/(0 - 4) = 1, the greatest value",
)
assert got == 1
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FP 3, a 3, b 4: (sqrt 72 - 9)/(8 - 9) = 9 - 6 sqrt 2",
)
assert close(got, 9 - 6 * D(2).sqrt())
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 3, FP 1, a 4, b 3: (sqrt 36 - 4)/(9 - 4) = 2/5",
)
assert close(got, D(2) / 5)
got = add(
    "lone",
    [1.0] + [0.0] * 9,
    [1.0, 1.0] + [0.0] * 8,
    "TPR 1, FPR 1/9: TP 1, FP 1, a 1, b 9: (sqrt 9 - 1)/(9 - 1) = 1/4",
)
assert got == D(1) / 4
rng = random.Random(487)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(487), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"prevalence_threshold.{cid}",
            "op": "prevalence_threshold",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("truth_all_zero", "truth has no 1: a = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])
err("truth_all_one", "truth has no 0: b = 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])
err(
    "equal_rates",
    "one of each cell: TPR = FPR = 1/2",
    truth=[1.0, 1.0, 0.0, 0.0],
    decision=[1.0, 0.0, 1.0, 0.0],
)


doc = {
    "schema": 1,
    "suite": "prevalence_threshold",
    "description": "The prevalence threshold (conventions: the prevalence threshold; ADR 0487).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "prevalence_threshold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/prevalence_threshold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
