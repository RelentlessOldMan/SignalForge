"""Writes vectors/cases/austin_colwell_coefficient.json, stdlib only.

The Austin-Colwell coefficient (conventions: the Austin-Colwell coefficient; ADR 0448): the
2x2 table counted directly, the arcsine found in 40-digit decimals as an arctangent by its
halved series, pi from Machin's formula.

Run from the repo root: python vectors/generators/austin_colwell_coefficient.py [--check]
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


def sin(v):
    total, term, i = D(0), v, 1
    while abs(term) > D("1e-45"):
        total += term
        term = -term * v * v / ((i + 1) * (i + 2))
        i += 2
    return total


def atan(z):
    """arctan of z >= 0: halved until small, then its series."""
    if z > 1:
        return PI / 2 - atan(1 / z)
    k = 0
    while z > D("0.01"):
        z = z / (1 + (1 + z * z).sqrt())
        k += 1
    total, term, i = D(0), z, 1
    while abs(term) > D("1e-45"):
        total += term / i
        term = -term * z * z
        i += 2
    return total * 2**k


def asin_sqrt(p):
    """asin of the root of p in [0, 1], as atan(sqrt(p/(1 - p))), so well conditioned."""
    if p == 1:
        return PI / 2
    return atan((p / (1 - p)).sqrt())


cases = []


def add(cid, t, d, why):
    agree = sum(1 for a, b in zip(t, d) if a == b)
    q = 2 * asin_sqrt(D(agree) / len(t)) / PI
    cases.append(
        {
            "id": f"austin_colwell_coefficient.{cid}",
            "op": "austin_colwell_coefficient",
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
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "all agree: p 1, asin 1 = pi/2, so 1"
)
assert close(got, D(1))
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "none agree: p 0, so 0")
assert close(got, D(0))
got = add(
    "half", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "p 1/2: asin(sqrt(1/2)) = pi/4, so 1/2"
)
assert close(got, D(1) / 2)
got = add("quarter", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 1.0], "p 1/4: asin(1/2) = pi/6, so 1/3")
assert close(got, D(1) / 3)
got = add(
    "three_quarters",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0],
    "p 3/4: asin(sqrt 3/2) = pi/3, so 2/3",
)
assert close(got, D(2) / 3)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: p 4/5, the value v with sin(pi v/2)^2 = 4/5",
)
assert abs(sin(PI * got / 2) ** 2 - D(4) / 5) < D("1e-35")
got = add("constant", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "truth all 1, TP 2, FN 1: p 2/3, no error")
assert abs(sin(PI * got / 2) ** 2 - D(2) / 3) < D("1e-35")
rng = random.Random(448)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(448), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"austin_colwell_coefficient.{cid}",
            "op": "austin_colwell_coefficient",
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
    "suite": "austin_colwell_coefficient",
    "description": "The Austin-Colwell coefficient (conventions: the Austin-Colwell"
    " coefficient; ADR 0448).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "austin_colwell_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/austin_colwell_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
