"""Writes vectors/cases/minkowski_distance.json, stdlib only.

The Minkowski distance (conventions: Minkowski distance; ADR 0419): the differences exact in
rationals, the powers in 40-digit decimal, with no scaling.

Run from the repo root: python vectors/generators/minkowski_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
decimal.getcontext().prec = 40
D = decimal.Decimal
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, y, order, why):
    s = D(0)
    for a, b in zip(x, y):
        d = abs(Fr(a) - Fr(b))
        if d != 0:
            s += (D(order) * dec(d).ln()).exp()
    r = D(0) if s == 0 else (s.ln() / D(order)).exp()
    cases.append(
        {
            "id": f"minkowski_distance.{cid}",
            "op": "minkowski_distance",
            "args": {"x": x, "y": y, "order": order},
            "expected": float(r),
            "tol": TOL,
            "source": why,
        }
    )
    return r


def close(a, b):
    return abs(a - b) <= abs(b) * D(10) ** -30


got = add("same", [1.0, -2.0], [1.0, -2.0], 2.0, "equal vectors: 0")
assert got == 0
got = add("city_block", [0.0, 0.0], [3.0, 4.0], 1.0, "order 1: 3 + 4 = 7")
assert close(got, D(7))
got = add("euclid", [0.0, 0.0], [3.0, 4.0], 2.0, "order 2: the 3-4-5 triangle, 5")
assert close(got, D(5))
got = add("cubic", [1.0, -1.0], [-2.0, 3.0], 3.0, "order 3: (27 + 64)^(1/3), the cube root of 91")
assert close(got, (D(91).ln() / 3).exp())
got = add(
    "huge",
    [1e300, 0.0],
    [0.0, 1e300],
    2.0,
    "order 2 with differences of 1e300, whose squares overflow a double: sqrt 2 · 1e300",
)
assert close(got, D(2).sqrt() * dec(Fr(1e300)))
got = add(
    "tiny",
    [3e-300, 0.0],
    [0.0, 4e-300],
    2.0,
    "order 2 with differences near 1e-300, whose squares underflow: 5e-300",
)
assert abs(got - D("5e-300")) < D("1e-314")
rng = random.Random(419)
x = [rng.randint(-20, 20) / 4 for _ in range(16)]
y = [rng.randint(-20, 20) / 4 for _ in range(16)]
add("random", x, y, 2.5, "16 quarters each from random.Random(419), order 2.5")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 1.0, 0.0], "order": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"minkowski_distance.{cid}",
            "op": "minkowski_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("order_low", "order must be at least 1", order=0.5)
err("order_inf", "order must be finite", order="inf")
err("empty", "x needs a value", x=[], y=[])
err("lengths", "x and y must match", y=[1.0, 1.0])
err("not_finite", "values must be finite", x=[1.0, "nan", 1.0])
err("overflow", "the difference 1e308 - (-1e308) overflows", x=[1e308], y=[-1e308])

for c in cases:  # below the absolute tolerance, only a relative one can fail
    if "expected" in c and 0 < abs(c["expected"]) < TOL["abs"]:
        c["tol"] = {"abs": 0.0, "rel": TOL["rel"]}

doc = {
    "schema": 1,
    "suite": "minkowski_distance",
    "description": "The Minkowski distance (conventions: Minkowski distance; ADR 0419).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "minkowski_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/minkowski_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
