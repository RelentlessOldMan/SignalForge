"""Writes vectors/cases/binary_g_statistic.json, stdlib only.

The G statistic of two binary records (conventions: the G statistic of two binary
records; ADR 0481): the 2x2 table counted directly, each nonzero cell's term
c·ln(n·c / (row·column)) formed with the log of an exact rational correctly rounded in
40-digit decimals, summed and doubled.

Run from the repo root: python vectors/generators/binary_g_statistic.py [--check]
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

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    n, na, nb = len(t), tp + fn, tp + fp
    q = D(0)
    for c, ra, kb in ((tp, na, nb), (fn, na, n - nb), (fp, n - na, nb), (tn, n - na, n - nb)):
        if c > 0:
            x = Fr(n * c, ra * kb)
            q += c * (D(x.numerator) / D(x.denominator)).ln()
    q *= 2
    cases.append(
        {
            "id": f"binary_g_statistic.{cid}",
            "op": "binary_g_statistic",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


LN2, LN3 = D(2).ln(), D(3).ln()
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "TP 2, TN 2, margins 2: 2 (2 ln 2 + 2 ln 2) = 8 ln 2",
)
assert close(got, 8 * LN2)
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2, margins 2: 8 ln 2")
assert close(got, 8 * LN2)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell, margins 2: every log is ln 1, 0",
)
assert got == 0
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2 (3, 2), FN 1 (3, 4), TN 3 (3, 4): 2 (2 ln 2 - ln 2 + 3 ln(3/2)) = 6 ln 3 - 4 ln 2",
)
assert close(got, 6 * LN3 - 4 * LN2)
got = add(
    "lone",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    "n 4, TP 1 (1, 1), TN 3 (3, 3): 2 (ln 4 + 3 ln(4/3)) = 16 ln 2 - 6 ln 3",
)
assert close(got, 16 * LN2 - 6 * LN3)
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1: TP 2 ln(6/6), FN 1 ln(3/3), 0, no error",
)
assert got == 0
got = add("all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "TN 3 (3, 3): ln 1, 0, no error")
assert got == 0
rng = random.Random(481)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(481), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"binary_g_statistic.{cid}",
            "op": "binary_g_statistic",
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
    "suite": "binary_g_statistic",
    "description": "The G statistic of two binary records (conventions: the G statistic"
    " of two binary records; ADR 0481).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "binary_g_statistic.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/binary_g_statistic.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
