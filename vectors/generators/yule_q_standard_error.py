"""Writes vectors/cases/yule_q_standard_error.json, stdlib only.

The standard error of Yule's Q (conventions: the standard error of Yule's Q; ADR 0495):
the 2x2 table counted directly, 2 sqrt(xy N) / (x + y)^2 with the square root in 40-digit
decimals.

Run from the repo root: python vectors/generators/yule_q_standard_error.py [--check]
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
    x, y = tp * tn, fn * fp
    num = fn * fp * tn + tp * fp * tn + tp * fn * tn + tp * fn * fp
    q = 2 * D(x * y * num).sqrt() / D((x + y) ** 2)
    cases.append(
        {
            "id": f"yule_q_standard_error.{cid}",
            "op": "yule_q_standard_error",
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
    "one of each cell: Q 0, (1/2) 1 sqrt 4 = 1",
)
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, FN 1, FP 1, TN 4: Q 15/17, (1/2)(64/289) sqrt(5/2) = 16 sqrt 10/289",
)
assert close(got, 16 * D(10).sqrt() / 289)
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 1, TN 2: Q 3/5, (1/2)(16/25) sqrt 3 = 8 sqrt 3/25",
)
assert close(got, 8 * D(3).sqrt() / 25)
got = add(
    "fours",
    [1.0] * 8 + [0.0] * 8,
    [1.0] * 4 + [0.0] * 4 + [1.0] * 4 + [0.0] * 4,
    "four of each cell: Q 0, (1/2) 1 sqrt 1 = 1/2",
)
assert got == D(1) / 2
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: Q -1/5, (1/2)(24/25) sqrt(17/6) = 2 sqrt 102/25",
)
assert close(got, 2 * D(102).sqrt() / 25)
rng = random.Random(495)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(495), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"yule_q_standard_error.{cid}",
            "op": "yule_q_standard_error",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_tp", "opposite records: TP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err("no_fp", "equal records: FP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[1.0, 0.0, 1.0, 0.0])
err(
    "no_fn",
    "every truth 1 caught: FN = 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 1.0, 1.0, 0.0],
)
err(
    "decision_all_one",
    "the decision has no 0: TN = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "yule_q_standard_error",
    "description": "The standard error of Yule's Q (conventions: the standard error of"
    " Yule's Q; ADR 0495).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "yule_q_standard_error.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/yule_q_standard_error.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
