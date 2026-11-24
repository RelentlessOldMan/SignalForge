"""Writes vectors/cases/lloyd_mean_crowding.json, stdlib only.

Lloyd's mean crowding (conventions: Lloyd's mean crowding; ADR 0609): sum(x (x - 1))/sum(x)
with fractions, straight from the definition.

Run from the repo root: python vectors/generators/lloyd_mean_crowding.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, counts, why):
    xs = [Fr(c) for c in counts]
    f = sum(c * (c - 1) for c in xs) / sum(xs)
    cases.append(
        {
            "id": f"lloyd_mean_crowding.{cid}",
            "op": "lloyd_mean_crowding",
            "args": {"counts": counts},
            "expected": float(f) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add("even", [2.0, 2.0, 2.0], "each individual has one other: 1") == 1
assert add("one_unit", [5.0], "five in one unit: four others each") == 4
assert add("singles", [1.0, 1.0, 1.0, 0.0], "no two share a unit: 0") == 0
assert add("clumped", [0.0, 0.0, 6.0], "all six in one unit: 5") == 5
assert add("mixed", [1.0, 2.0, 3.0], "(0 + 2 + 6)/6 = 4/3") == Fr(4, 3)
assert add("uneven", [4.0, 0.0, 1.0, 0.0, 3.0], "(12 + 0 + 6)/8 = 9/4") == Fr(9, 4)
assert (
    add("huge", [1e308, 1e308], "the sums would overflow: 1e308 - 1, which rounds to 1e308")
    == Fr(1e308) - 1
)
rng = random.Random(609)
counts = [float(rng.choice([0, 0, 1, 2, 3, 7])) for _ in range(30)]
add("random", counts, "30 counts from random.Random(609).choice([0, 0, 1, 2, 3, 7])")


def err(cid, why, counts):
    cases.append(
        {
            "id": f"lloyd_mean_crowding.{cid}",
            "op": "lloyd_mean_crowding",
            "args": {"counts": counts},
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a unit", [])
err("negative", "counts must be at least 0", [1.0, -1.0, 2.0])
err("all_zero", "the total must be above 0", [0.0, 0.0])
err("not_whole", "counts must be whole numbers", [1.0, 2.5])

doc = {
    "schema": 1,
    "suite": "lloyd_mean_crowding",
    "description": "Lloyd's mean crowding (conventions: Lloyd's mean crowding; ADR 0609).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lloyd_mean_crowding.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lloyd_mean_crowding.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
