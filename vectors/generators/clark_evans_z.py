"""Writes vectors/cases/clark_evans_z.json, stdlib only.

The Clark-Evans test statistic (conventions: the Clark-Evans test statistic; ADR 0617): the
mean distance with fractions, then (mean - 1/(2 sqrt(density)))/sigma with
sigma = sqrt((4 - pi)/(4 pi density n)), pi from Machin's formula, in 60-digit decimals.

Run from the repo root: python vectors/generators/clark_evans_z.py [--check]
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
TOL = {"abs": 1e-13, "rel": 1e-13}
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


def add(cid, distances, density, why):
    n = len(distances)
    mean = sum(Fr(d) for d in distances) / n
    r_e = 1 / (2 * D(density).sqrt())
    sigma = ((4 - PI) / (4 * PI * D(density) * n)).sqrt()
    v = (D(mean.numerator) / D(mean.denominator) - r_e) / sigma
    cases.append(
        {
            "id": f"clark_evans_z.{cid}",
            "op": "clark_evans_z",
            "args": {"distances": distances, "density": density},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -45 * max(1, abs(b))


C3 = (3 * PI / (4 - PI)).sqrt()
assert abs(PI - D("3.14159265358979323846264338327950288419716939937510582097494")) < D(10) ** -55
assert near(add("random_mean", [0.5, 0.5], 1.0, "the mean for a random pattern: 0"), 0)
assert near(add("lattice", [1.0, 1.0, 1.0], 1.0, "R = 2, n = 3: sqrt(3 pi/(4 - pi))"), C3)
assert near(
    add("coincident", [0.0, 0.0], 1.0, "R = 0, n = 2: -sqrt(2 pi/(4 - pi))"),
    -(2 * PI / (4 - PI)).sqrt(),
)
assert near(add("quarter", [0.25], 16.0, "R = 2, n = 1: sqrt(pi/(4 - pi))"), (PI / (4 - PI)).sqrt())
assert near(
    add("clumped", [0.25, 0.25, 0.625], 4.0, "R = 3/2, n = 3: sqrt(3 pi/(4 - pi))/2"), C3 / 2
)
assert near(
    add("huge", [1e300, 1e300], 0.25, "R = 1e300, n = 2: (1e300 - 1) sqrt(2 pi/(4 - pi))"),
    (D(1e300) - 1) * (2 * PI / (4 - PI)).sqrt(),
)
rng = random.Random(617)
distances = [rng.uniform(0.0, 2.0) for _ in range(25)]
density = rng.uniform(0.5, 3.0)
add(
    "random",
    distances,
    density,
    "25 distances from random.Random(617).uniform(0, 2), then the density from uniform(0.5, 3)",
)


def err(cid, why, distances=None, density=1.0):
    args = {"distances": [0.5, 1.0] if distances is None else distances, "density": density}
    cases.append(
        {
            "id": f"clark_evans_z.{cid}",
            "op": "clark_evans_z",
            "args": args,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a distance", distances=[])
err("negative", "distances must be at least 0", distances=[1.0, -0.5])
err("zero_density", "the density must be above 0", density=0.0)
err("negative_density", "the density must be above 0", density=-1.0)
err(
    "overflow",
    "R = 1e308 overflows when multiplied by sqrt(2 pi/(4 - pi))",
    distances=[1e308, 1e308],
    density=0.25,
)

doc = {
    "schema": 1,
    "suite": "clark_evans_z",
    "description": "The Clark-Evans test statistic (conventions: the Clark-Evans test "
    "statistic; ADR 0617).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "clark_evans_z.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/clark_evans_z.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
