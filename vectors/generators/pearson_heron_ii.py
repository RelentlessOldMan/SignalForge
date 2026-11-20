"""Writes vectors/cases/pearson_heron_ii.json, stdlib only.

The Pearson-Heron II coefficient (conventions: Pearson-Heron II coefficient; ADR 0443): the
2x2 table counted directly, the roots and the cosine's Taylor series in 40-digit decimals,
pi from Machin's formula.

Run from the repo root: python vectors/generators/pearson_heron_ii.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40
TOL = {"abs": 1e-15, "rel": 1e-14}


def atan_inv(k):
    """arctan(1/k) by its series."""
    total, term, i, sign = D(0), D(1) / k, 1, 1
    while term != 0:
        total += sign * term / i
        term /= k * k
        i += 2
        sign = -sign
    return total


PI = 16 * atan_inv(5) - 4 * atan_inv(239)


def cos(v):
    total, term, i = D(0), D(1), 0
    while abs(term) > D("1e-45"):
        total += term
        term = -term * v * v / ((i + 1) * (i + 2))
        i += 2
    return total


cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = sum(1 for a, b in zip(t, d) if a == 0 and b == 0)
    sx, sy = D(tp * tn).sqrt(), D(fn * fp).sqrt()
    q = cos(PI * sy / (sx + sy))
    cases.append(
        {
            "id": f"pearson_heron_ii.{cid}",
            "op": "pearson_heron_ii",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(v, want):
    return abs(v - want) < D("1e-35")


got = add(
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, TN 2, no mismatch: cos 0 = 1"
)
assert got == 1
got = add(
    "opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2, no match: cos pi = -1"
)
assert close(got, D(-1))
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: cos(pi/2) = 0"
)
assert close(got, D(0))
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: cos(pi/(sqrt 2 + 1)) = cos(pi (sqrt 2 - 1))",
)
assert close(got, cos(PI * (D(2).sqrt() - 1)))
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: cos(pi/5) = (1 + sqrt 5)/4",
)
assert close(got, (1 + D(5).sqrt()) / 4)
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 2, TN 2, FN 1, FP 1: cos(pi/3) = 1/2",
)
assert close(got, D(1) / 2)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 1, FN 2, FP 0, TN 2: FP empty gives cos 0 = 1",
)
assert got == 1
rng = random.Random(443)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(443), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"pearson_heron_ii.{cid}",
            "op": "pearson_heron_ii",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "constant",
    "truth all 1: TN and FP are 0, so both products are 0",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 0.0, 1.0],
)

doc = {
    "schema": 1,
    "suite": "pearson_heron_ii",
    "description": "The Pearson-Heron II coefficient (conventions: Pearson-Heron II"
    " coefficient; ADR 0443).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pearson_heron_ii.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pearson_heron_ii.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
