"""Writes vectors/cases/cohen_h_standard_error.json, stdlib only.

The standard error of Cohen's h (conventions: the standard error of Cohen's h; ADR 0507):
the decision's 1s and 0s counted directly, 1/n1 + 1/n2 in rationals and the square root
in 40-digit decimals.

Run from the repo root: python vectors/generators/cohen_h_standard_error.py [--check]
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
    f = Fr(1, tp + fp) + Fr(1, fn + tn)
    q = (D(f.numerator) / D(f.denominator)).sqrt()
    cases.append(
        {
            "id": f"cohen_h_standard_error.{cid}",
            "op": "cohen_h_standard_error",
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
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "two 1s, two 0s: sqrt(1/2 + 1/2) = 1"
)
assert got == 1
got = add(
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "two 1s, two 0s: 1, whatever the truth"
)
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "five 1s, five 0s: sqrt(2/5)",
)
assert close(got, (D(2) / 5).sqrt())
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "five 1s, two 0s: sqrt(1/5 + 1/2) = sqrt(7/10)",
)
assert close(got, (D(7) / 10).sqrt())
got = add("single_one", [1.0, 0.0], [1.0, 0.0], "one 1, one 0: sqrt 2, the largest")
assert close(got, D(2).sqrt())
rng = random.Random(507)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(507), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cohen_h_standard_error.{cid}",
            "op": "cohen_h_standard_error",
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
    "suite": "cohen_h_standard_error",
    "description": "The standard error of Cohen's h (conventions: the standard error of"
    " Cohen's h; ADR 0507).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cohen_h_standard_error.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cohen_h_standard_error.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
