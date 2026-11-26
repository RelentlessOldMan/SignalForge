"""Writes vectors/cases/eberhardt_index.json, stdlib only.

Eberhardt's index (conventions: Eberhardt's index; ADR 0620): the sums with fractions.

Run from the repo root: python vectors/generators/eberhardt_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, u, why):
    s1 = sum(Fr(d) for d in u)
    s2 = sum(Fr(d) ** 2 for d in u)
    v = len(u) * s2 / (s1 * s1)
    cases.append(
        {
            "id": f"eberhardt_index.{cid}",
            "op": "eberhardt_index",
            "args": {"point_distances": u},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


assert add("single", [2.5], "one distance: 1") == 1
assert add("equal", [3.0, 3.0, 3.0], "all equal, the least: 1") == 1
assert add("one_nonzero", [0.0, 0.0, 0.0, 4.0], "one above 0, the most: n = 4") == 4
assert add("two", [1.0, 3.0], "2 * 10/16 = 5/4") == Fr(5, 4)
assert add("three", [1.0, 2.0, 3.0], "3 * 14/36 = 7/6") == Fr(7, 6)
assert add("huge", [1e300, 3e300], "the squares would overflow: 5/4") == Fr(5, 4)
assert add(
    "tiny", [5e-324, 1e-323], "the smallest doubles, 1 and 2 of them: 2 * 5/9 = 10/9"
) == Fr(10, 9)
rng = random.Random(620)
add(
    "random",
    [rng.uniform(0.0, 2.0) for _ in range(25)],
    "25 distances from random.Random(620).uniform(0, 2)",
)

# Krebs, Ecological Methodology (2017 web edition), Box 5.2: 16 point-to-tree distances (m) of
# white spruce. Krebs gives sums 154.9 and 1694.93, variance 13.020 over n - 1, and eq. 6.14
# I_E = (s/mean)^2 + 1 = 1.14 with that n - 1 variance; the index here divides by n, so
# 1 + (I - 1) n/(n - 1) must give his 1.14.
KREBS = [
    12.6,
    9.3,
    7.5,
    16.2,
    8.8,
    10.1,
    6.2,
    1.5,
    14.3,
    9.6,
    11.3,
    8.9,
    6.3,
    13.9,
    10.8,
    7.6,
]
assert sum(Fr(str(d)) for d in KREBS) == Fr("154.9")
assert sum(Fr(str(d)) ** 2 for d in KREBS) == Fr("1694.93")
krebs = add(
    "krebs_spruce",
    KREBS,
    "Krebs (2017) Box 5.2 spruce distances; with the n - 1 variance his eq. 6.14 gives 1.14",
)
assert round(float(1 + (krebs - 1) * Fr(16, 15)), 2) == 1.14


def err(cid, why, u):
    cases.append(
        {
            "id": f"eberhardt_index.{cid}",
            "op": "eberhardt_index",
            "args": {"point_distances": u},
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a distance above 0", [])
err("all_zero", "there must be a distance above 0", [0.0, 0.0])
err("negative", "distances must be at least 0", [1.0, -0.5])

doc = {
    "schema": 1,
    "suite": "eberhardt_index",
    "description": "Eberhardt's index (conventions: Eberhardt's index; ADR 0620).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "eberhardt_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/eberhardt_index.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
