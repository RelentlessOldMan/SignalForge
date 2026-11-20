"""Writes vectors/cases/stiles_coefficient.json, stdlib only.

Stiles' coefficient (conventions: Stiles' coefficient; ADR 0451): the 2x2 table counted
directly, the argument formed in rationals as
(|TP TN - FN FP| - n/2)^2 n / (|A| |B| (n - |A|)(n - |B|)), its log10 correctly rounded in
40-digit decimals.

Run from the repo root: python vectors/generators/stiles_coefficient.py [--check]
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
    n = len(t)
    na, nb = tp + fn, tp + fp
    arg = (abs(tp * tn - fn * fp) - Fr(n, 2)) ** 2 * n / (na * nb * (n - na) * (n - nb))
    q = (D(arg.numerator) / D(arg.denominator)).log10()
    cases.append(
        {
            "id": f"stiles_coefficient.{cid}",
            "op": "stiles_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 2, TN 2: (4 - 2)^2 4/(2 2 2 2) = 1, log10 1 = 0",
)
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, FN 2, FP 2: (4 - 2)^2 4/16 = 1, so 0, as for identical",
)
assert got == 0
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: (0 - 2)^2 4/16 = 1, so 0; the correction makes it grow",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: (1 - 5/2)^2 5/(2 2 3 3) = 5/16",
)
assert abs(got - (D(5) / 16).log10()) < D("1e-35")
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: (15 - 5)^2 10/(5 5 5 5) = 8/5",
)
assert abs(got - (D(8) / 5).log10()) < D("1e-35")
got = add(
    "hundred",
    [1.0] * 10 + [0.0] * 10,
    [1.0] * 10 + [0.0] * 10,
    "n 20, TP 10, TN 10: (100 - 10)^2 20/10^4 = 81/5, log10 81/5",
)
assert abs(got - (D(81) / 5).log10()) < D("1e-35")
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, FN 1, FP 0, TN 3: (6 - 3)^2 6/(3 2 3 4) = 3/4",
)
assert abs(got - (D(3) / 4).log10()) < D("1e-35")
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "TP 0, FN 1, FP 3, TN 0: (3 - 2)^2 4/(1 3 3 1) = 4/9",
)
assert abs(got - (D(4) / 9).log10()) < D("1e-35")
rng = random.Random(451)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(451), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"stiles_coefficient.{cid}",
            "op": "stiles_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_decision_one", "decision all 0: |B| = 0", decision=[0.0, 0.0, 0.0])
err("all_one", "truth all 1: n - |A| = 0", truth=[1.0, 1.0, 1.0])
err(
    "half",
    "TP 1, FN 0, FP 1, TN 2: |2 - 0| = n/2, the argument is 0",
    truth=[1.0, 0.0, 0.0, 0.0],
    decision=[1.0, 1.0, 0.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "stiles_coefficient",
    "description": "Stiles' coefficient (conventions: Stiles' coefficient; ADR 0451).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "stiles_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/stiles_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
