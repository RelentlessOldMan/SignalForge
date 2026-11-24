"""Writes vectors/cases/lloyd_mean_crowding.json, stdlib only.

Green's index of dispersion (conventions: Green's index of dispersion; ADR 0611): the mean
and the sample variance from their definitions, and (s^2/m - 1)/(sum(x) - 1), with
fractions.

Run from the repo root: python vectors/generators/lloyd_mean_crowding.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, counts, why):
    xs = [Fr(c) for c in counts]
    n = len(xs)
    m = sum(xs) / n
    var = sum((c - m) ** 2 for c in xs) / (n - 1)
    f = (var / m - 1) / (sum(xs) - 1)
    cases.append(
        {
            "id": f"green_index.{cid}",
            "op": "green_index",
            "args": {"counts": counts},
            "expected": float(f) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add("even", [2.0, 2.0, 2.0], "no variance: -1/(6 - 1) = -1/5") == Fr(-1, 5)
assert add("clumped", [0.0, 0.0, 6.0], "all in one unit: s^2/m = 12/2, (6 - 1)/5 = 1") == 1
assert add("two_units", [0.0, 3.0], "all in one unit: s^2/m = 4.5/1.5, (3 - 1)/2 = 1") == 1
assert add("mixed", [1.0, 2.0, 3.0], "m 2, s^2 1: (1/2 - 1)/5 = -1/10") == Fr(-1, 10)
assert add("uneven", [4.0, 0.0, 1.0, 0.0, 3.0], "m 8/5, s^2 33/10: (33/16 - 1)/7 = 17/112") == Fr(
    17, 112
)
assert add("singles", [1.0, 1.0, 0.0, 0.0], "m 1/2, s^2 1/3: (2/3 - 1)/1 = -1/3") == Fr(-1, 3)
assert add("huge", [1e308, 0.0], "the sums would overflow: all in one unit, 1") == 1
rng = random.Random(611)
counts = [float(rng.choice([0, 0, 1, 2, 3, 7])) for _ in range(30)]
add("random", counts, "30 counts from random.Random(611).choice([0, 0, 1, 2, 3, 7])")


def err(cid, why, counts):
    cases.append(
        {
            "id": f"green_index.{cid}",
            "op": "green_index",
            "args": {"counts": counts},
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a unit", [])
err("one_unit", "the variance needs at least two units", [5.0])
err("total_one", "the total must be above 1", [1.0, 0.0])
err("negative", "counts must be at least 0", [1.0, -1.0, 2.0])
err("all_zero", "the total must be above 0", [0.0, 0.0])
err("not_whole", "counts must be whole numbers", [1.0, 2.5])

doc = {
    "schema": 1,
    "suite": "lloyd_mean_crowding",
    "description": "Green's index of dispersion (conventions: Green's index of dispersion; "
    "ADR 0611).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "green_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/green_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
