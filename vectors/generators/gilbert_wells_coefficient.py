"""Writes vectors/cases/gilbert_wells_coefficient.json, stdlib only.

The Gilbert-Wells coefficient (conventions: the Gilbert-Wells coefficient; ADR 0463): the
2x2 table counted directly, the lift n·TP / (|A|·|B|) formed in rationals, its natural log
correctly rounded in 40-digit decimals.

Run from the repo root: python vectors/generators/gilbert_wells_coefficient.py [--check]
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
    lift = Fr(len(t) * tp, (tp + fn) * (tp + fp))
    q = (D(lift.numerator) / D(lift.denominator)).ln()
    cases.append(
        {
            "id": f"gilbert_wells_coefficient.{cid}",
            "op": "gilbert_wells_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


LN2 = D(2).ln()
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 2, |A| = |B| = 2: ln(8/4) = ln 2",
)
assert close(got, LN2)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 1, |A| = |B| = 2: ln(4/4) = 0, independence",
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, |A| = |B| = 5: ln(40/25) = ln(8/5)",
)
assert close(got, 3 * LN2 - D(5).ln())
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2, |A| 3, |B| 2: ln(12/6) = ln 2",
)
assert close(got, LN2)
got = add(
    "lone",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    "n 4, TP 1, |A| = |B| = 1: ln 4 = 2 ln 2, the most for n 4",
)
assert close(got, 2 * LN2)
got = add(
    "below",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 1.0],
    "n 4, TP 1, |A| 2, |B| 3: ln(4/6) = ln(2/3), below independence",
)
assert close(got, LN2 - D(3).ln())
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1, n 3, TP 2, |B| 2: ln(6/6) = 0, no error",
)
assert got == 0
rng = random.Random(463)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(463), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gilbert_wells_coefficient.{cid}",
            "op": "gilbert_wells_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "no_shared_one",
    "TP = 0: the log of 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[0.0, 1.0, 0.0, 1.0],
)
err("all_zero", "no 1 in either record: TP = 0", truth=[0.0, 0.0, 0.0], decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "gilbert_wells_coefficient",
    "description": "The Gilbert-Wells coefficient (conventions: the Gilbert-Wells"
    " coefficient; ADR 0463).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gilbert_wells_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/gilbert_wells_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
