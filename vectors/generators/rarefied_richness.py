"""Writes vectors/cases/rarefied_richness.json, stdlib only.

The rarefied richness (conventions: the rarefied richness; ADR 0552): each miss
probability C(N - x, n)/C(N, n) formed exactly from binomial coefficients.

Run from the repo root: python vectors/generators/rarefied_richness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, size, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    whole = math.comb(total, size)
    q = sum(1 - Fr(math.comb(total - a, size), whole) for a in v if a > 0)
    cases.append(
        {
            "id": f"rarefied_richness.{cid}",
            "op": "rarefied_richness",
            "args": {"samples": x, "size": size},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("one_drawn", [3.0, 1.0, 2.0], 1, "one individual is one kind") == 1
assert add("all_drawn", [3.0, 0.0, 1.0, 2.0], 6, "every individual: every kind") == 3
assert add("two_of_four", [3.0, 1.0], 2, "miss 1: C(3,2)/C(4,2) = 1/2; miss 3: 0") == (Fr(3, 2))
assert add("ramp", [1.0, 2.0, 3.0], 2, "misses 10/15, 6/15, 3/15: 3 - 19/15") == Fr(26, 15)
assert add("even", [2.0, 2.0, 2.0], 3, "each missed with C(4,3)/C(6,3) = 1/5: 12/5") == (Fr(12, 5))
assert add(
    "mixed",
    [5.0, 1.0, 1.0, 0.0, 2.0],
    4,
    "N = 9, n = 4: C(4,4), C(8,4), C(8,4), C(7,4) over C(9,4)",
) == 4 - Fr(1 + 70 + 70 + 35, 126)
add("larger", [40.0, 25.0, 0.0, 10.0, 25.0, 1.0], 30, "N = 101, n = 30")
rng = random.Random(552)
x = [float(rng.randint(0, 20)) for _ in range(30)]
add("random", x, 50, "30 whole values from random.Random(552).randint(0, 20), n = 50")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "size": 2}
    base.update(args)
    cases.append(
        {
            "id": f"rarefied_richness.{cid}",
            "op": "rarefied_richness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000 000", samples=[10000000.0, 1.0])
err("size_zero", "size must be at least 1", size=0)
err("size_negative", "size must be at least 1", size=-1)
err("size_above_total", "size must be at most the total", size=7)

doc = {
    "schema": 1,
    "suite": "rarefied_richness",
    "description": "The rarefied richness (conventions: the rarefied richness; ADR 0552).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rarefied_richness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/rarefied_richness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
