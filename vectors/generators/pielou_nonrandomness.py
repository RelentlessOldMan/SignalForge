"""Writes vectors/cases/pielou_nonrandomness.json, stdlib only.

Pielou's index of non-randomness (conventions: Pielou's index of non-randomness; ADR 0619):
the mean squared distance with fractions, times pi density with pi from Machin's formula, in
60-digit decimals.

Run from the repo root: python vectors/generators/pielou_nonrandomness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 60
TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def arctan_inv(k):
    # arctan(1/k) by its series, to the working precision.
    x = D(1) / k
    term = x
    total = x
    j = 1
    while abs(term) > D(10) ** -70:
        term = -term * x * x
        total += term / (2 * j + 1)
        j += 1
    return total


PI = 4 * (4 * arctan_inv(5) - arctan_inv(239))
assert abs(PI - D("3.14159265358979323846264338327950288419716939937510582097494")) < D(10) ** -55


def add(cid, u, density, why):
    m = sum(Fr(d) ** 2 for d in u) / len(u)
    v = PI * D(density) * D(m.numerator) / D(m.denominator)
    cases.append(
        {
            "id": f"pielou_nonrandomness.{cid}",
            "op": "pielou_nonrandomness",
            "args": {"point_distances": u, "density": density},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -45 * max(1, abs(b))


assert near(add("unit", [1.0], 1.0, "pi * 1 * 1: pi"), PI)
assert near(add("mean_square", [1.0, 3.0], 0.5, "mean square 5, pi * 0.5 * 5: 5 pi/2"), 5 * PI / 2)
assert near(
    add(
        "random_mean",
        [0.5, 0.5],
        4.0 / 3.141592653589793,
        "density 4/pi (as a double), mean square 1/4: about 1",
    ),
    PI * D(4.0 / 3.141592653589793) / 4,
)
assert add("coincident", [0.0, 0.0], 2.0, "every point on an individual: 0") == 0
assert near(
    add("huge", [1e200], 1e-300, "the square would overflow: pi * 1e100"),
    PI * D(1e-300) * D(1e200) ** 2,
)
assert near(
    add("tiny", [1e-200, 0.0], 1e300, "the square would underflow: pi * 1e-100/2"),
    PI * D(1e300) * D(1e-200) ** 2 / 2,
)
assert near(
    add("dense", [1e-200], 1e308, "pi times the density would overflow: pi * 1e-92"),
    PI * D(1e308) * D(1e-200) ** 2,
)
assert near(
    add(
        "square_near_top",
        [1.5e154, 0.0],
        1 / 3.141592653589793,
        "t sqrt(pi density) squared would overflow: 1.125e308 (density 1/pi as a double)",
    ),
    PI * D(1 / 3.141592653589793) * D(1.5e154) ** 2 / 2,
)
assert near(
    add("sparse_large", [1e154] + [0.0] * 99, 1.0, "1e308 pi/100: about 3.14e306"),
    PI * D(1e154) ** 2 / 100,
)
assert near(
    add(
        "subnormal_density",
        [1e200],
        5e-324,
        "pi times a subnormal density would round: pi 2^-1074 1e400",
    ),
    PI * D(5e-324) * D(1e200) ** 2,
)
rng = random.Random(619)
u = [rng.uniform(0.0, 2.0) for _ in range(25)]
density = rng.uniform(0.05, 0.5)
add(
    "random",
    u,
    density,
    "25 distances from random.Random(619).uniform(0, 2), then the density from uniform(0.05, 0.5)",
)


def err(cid, why, u=None, density=1.0):
    args = {"point_distances": [0.5, 1.0] if u is None else u, "density": density}
    cases.append(
        {
            "id": f"pielou_nonrandomness.{cid}",
            "op": "pielou_nonrandomness",
            "args": args,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a distance", u=[])
err("negative", "distances must be at least 0", u=[1.0, -0.5])
err("zero_density", "the density must be above 0", density=0.0)
err("negative_density", "the density must be above 0", density=-1.0)
err("overflow", "pi * 1e300 * 1e10 overflows", u=[1e150, 1e150], density=1e10)

for c in cases:  # below the absolute tolerance, only a relative one can fail
    if "expected" in c and 0 < abs(c["expected"]) < TOL["abs"]:
        c["tol"] = {"abs": 0.0, "rel": TOL["rel"]}

doc = {
    "schema": 1,
    "suite": "pielou_nonrandomness",
    "description": "Pielou's index of non-randomness (conventions: Pielou's index of "
    "non-randomness; ADR 0619).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pielou_nonrandomness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pielou_nonrandomness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
