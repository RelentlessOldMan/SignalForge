"""Writes vectors/cases/clark_evans_ratio.json, stdlib only.

The Clark-Evans aggregation index (conventions: the Clark-Evans aggregation index;
ADR 0616): the mean distance with fractions, times 2 sqrt(density) with 60-digit decimals.

Run from the repo root: python vectors/generators/clark_evans_ratio.py [--check]
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
TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, distances, density, why):
    mean = sum(Fr(d) for d in distances) / len(distances)
    v = 2 * D(mean.numerator) / D(mean.denominator) * D(density).sqrt()
    cases.append(
        {
            "id": f"clark_evans_ratio.{cid}",
            "op": "clark_evans_ratio",
            "args": {"distances": distances, "density": density},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


assert add("random_mean", [0.5, 0.5], 1.0, "the mean for a random pattern, 1/2: 1") == 1
assert add("lattice", [1.0, 1.0, 1.0], 1.0, "mean 1 at density 1: 2") == 2
assert add("quarter", [0.25], 16.0, "2 * 1/4 * 4 = 2") == 2
assert add("coincident", [0.0, 0.0], 1.0, "every neighbour at the same place: 0") == 0
assert (
    add("clumped", [0.25, 0.25, 0.625], 4.0, "mean 3/8 at density 4: 2 * 3/8 * 2 = 3/2") == D(3) / 2
)
assert (
    abs(add("root_two", [1.0], 2.0, "2 * 1 * sqrt(2) = 2 sqrt(2)") - 2 * D(2).sqrt()) < D(10) ** -50
)
assert (
    abs(
        add("huge", [1e308, 1e308], 0.25, "the sum would overflow: 2 * 1e308 * 1/2 = 1e308")
        / D(1e308)
        - 1
    )
    < D(10) ** -50
)
assert add("tiny", [5e-324], 1.0, "the smallest double: 2 * 5e-324") == 2 * D(5e-324)
rng = random.Random(616)
distances = [rng.uniform(0.0, 2.0) for _ in range(25)]
density = rng.uniform(0.5, 3.0)
add(
    "random",
    distances,
    density,
    "25 distances from random.Random(616).uniform(0, 2), then the density from uniform(0.5, 3)",
)


def err(cid, why, distances=None, density=1.0):
    args = {"distances": [0.5, 1.0] if distances is None else distances, "density": density}
    cases.append(
        {
            "id": f"clark_evans_ratio.{cid}",
            "op": "clark_evans_ratio",
            "args": args,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a distance", distances=[])
err("negative", "distances must be at least 0", distances=[1.0, -0.5])
err("zero_density", "the density must be above 0", density=0.0)
err("negative_density", "the density must be above 0", density=-1.0)
err("overflow", "2 * 1e308 * 2 overflows", distances=[1e308], density=4.0)

doc = {
    "schema": 1,
    "suite": "clark_evans_ratio",
    "description": "The Clark-Evans aggregation index (conventions: the Clark-Evans "
    "aggregation index; ADR 0616).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "clark_evans_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/clark_evans_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
