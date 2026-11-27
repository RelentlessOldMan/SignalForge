"""Writes vectors/cases/coefficient_of_variation.json, stdlib only.

The coefficient of variation (conventions: the coefficient of variation; ADR 0513): the mean
and the population variance of dyadic values exact in rationals, the square root in
40-digit decimals.

Run from the repo root: python vectors/generators/coefficient_of_variation.py [--check]
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


def add(cid, x, why):
    v = [Fr(a) for a in x]
    n = len(v)
    mean = sum(v) / n
    f = sum((a - mean) ** 2 for a in v) / n / mean**2
    q = (D(f.numerator) / D(f.denominator)).sqrt()
    cases.append(
        {
            "id": f"coefficient_of_variation.{cid}",
            "op": "coefficient_of_variation",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("single", [5.0], "one value: 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "mean 1, variance (1 + 1 + 1 + 9)/4 = 3: sqrt 3")
assert close(got, D(3).sqrt())
got = add("two", [1.0, 3.0], "mean 2, variance 1: 1/2")
assert got == D(1) / 2
got = add("ramp", [1.0, 2.0, 3.0, 4.0], "mean 5/2, variance 5/4: sqrt 5/5")
assert close(got, D(5).sqrt() / 5)
got = add("negative_value", [-1.0, 2.0, 5.0], "mean 2, variance (9 + 0 + 9)/3 = 6: sqrt 6/2")
assert close(got, D(6).sqrt() / 2)
got = add(
    "halves",
    [0.5, 0.25, 0.25, 1.0],
    "mean 1/2, variance (0 + 1/16 + 1/16 + 1/4)/4 = 3/32: sqrt(3/8)",
)
assert close(got, (D(3) / 8).sqrt())
rng = random.Random(513)
x = [rng.randint(-16, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(513).randint(-16, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"coefficient_of_variation.{cid}",
            "op": "coefficient_of_variation",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("zero_mean", "the mean must be greater than 0", samples=[1.0, -1.0])
err("negative_mean", "the mean must be greater than 0", samples=[-1.0, -2.0, 0.5])

doc = {
    "schema": 1,
    "suite": "coefficient_of_variation",
    "description": "The coefficient of variation (conventions: the coefficient of variation;"
    " ADR 0513).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "coefficient_of_variation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/coefficient_of_variation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
