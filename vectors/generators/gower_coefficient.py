"""Writes vectors/cases/gower_coefficient.json, stdlib only.

Gower's coefficient (conventions: Gower's coefficient; ADR 0469): the 2x2 table counted
directly, the square of the value formed in rationals, its
square root correctly rounded in 40-digit decimals.

Run from the repo root: python vectors/generators/gower_coefficient.py [--check]
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

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    pa, pb = Fr(tp + fn, len(t)), Fr(tp + fp, len(t))
    na, nb, n = tp + fn, tp + fp, len(t)
    sq = Fr((tp + tn) ** 2, na * nb * (n - na) * (n - nb))
    q = (D(sq.numerator) / D(sq.denominator)).sqrt()
    cases.append(
        {
            "id": f"gower_coefficient.{cid}",
            "op": "gower_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - D(b.numerator) / D(b.denominator)) < D(10) ** -35


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP + TN 4, all margins 2: 4/sqrt(16) = 1",
)
assert got == 1
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "TP + TN 0: 0, the least value")
assert got == 0
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell, all margins 2: 2/sqrt(16) = 1/2",
)
assert close(got, Fr(1, 2))
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, all margins 5: 8/25",
)
assert close(got, Fr(8, 25))
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, TN 3, |A| 3, |B| 2: 5/sqrt(6 12), square 25/72",
)
assert close(got * got, Fr(25, 72))
got = add(
    "one_sided",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, TN 1, |A| 2, |B| 4: 3/sqrt(8 3), square 3/8",
)
assert close(got * got, Fr(3, 8))
got = add(
    "lone",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    "n 4, TP + TN 4, |A| = |B| = 1: 4/sqrt(1 1 3 3) = 4/3, above 1",
)
assert close(got, Fr(4, 3))
rng = random.Random(469)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(469), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gower_coefficient.{cid}",
            "op": "gower_coefficient",
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

doc = {
    "schema": 1,
    "suite": "gower_coefficient",
    "description": "Gower's coefficient (conventions: Gower's coefficient; ADR 0469).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gower_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gower_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
