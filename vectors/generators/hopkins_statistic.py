"""Writes vectors/cases/hopkins_statistic.json, stdlib only.

Hopkins' statistic (conventions: Hopkins' statistic; ADR 0618): the sums of squares with
fractions.

Run from the repo root: python vectors/generators/hopkins_statistic.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, u, w, why):
    a = sum(Fr(d) ** 2 for d in u)
    b = sum(Fr(d) ** 2 for d in w)
    v = a / (a + b)
    cases.append(
        {
            "id": f"hopkins_statistic.{cid}",
            "op": "hopkins_statistic",
            "args": {"point_distances": u, "individual_distances": w},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


assert add("equal", [1.0, 2.0], [2.0, 1.0], "the same distances: 1/2") == Fr(1, 2)
assert add("clumped", [3.0, 4.0], [0.0, 0.0, 1.0], "a = 25, b = 1: 25/26") == Fr(25, 26)
assert add("regular", [1.0], [2.0, 2.0], "a = 1, b = 8: 1/9") == Fr(1, 9)
assert add("one_each", [0.5], [1.5], "a = 1/4, b = 9/4: 1/10") == Fr(1, 10)
assert add("huge", [1e300, 1e300], [1e300], "the squares would overflow: 2/3") == Fr(2, 3)
assert add("tiny", [5e-324], [5e-324, 5e-324], "the smallest double: 1/3") == Fr(1, 3)
rng = random.Random(618)
u = [rng.uniform(0.0, 2.0) for _ in range(20)]
w = [rng.uniform(0.0, 1.0) for _ in range(20)]
add(
    "random",
    u,
    w,
    "20 point distances from random.Random(618).uniform(0, 2), then 20 individual distances "
    "from uniform(0, 1)",
)


def err(cid, why, u=None, w=None):
    args = {
        "point_distances": [0.5, 1.0] if u is None else u,
        "individual_distances": [1.0, 0.5] if w is None else w,
    }
    cases.append(
        {
            "id": f"hopkins_statistic.{cid}",
            "op": "hopkins_statistic",
            "args": args,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty_points", "there must be a point distance", u=[])
err("empty_individuals", "there must be an individual distance", w=[])
err("negative", "distances must be at least 0", u=[1.0, -0.5])
err("zero_points", "a point distance must be above 0", u=[0.0, 0.0])
err("zero_individuals", "an individual distance must be above 0", w=[0.0])

doc = {
    "schema": 1,
    "suite": "hopkins_statistic",
    "description": "Hopkins' statistic (conventions: Hopkins' statistic; ADR 0618).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hopkins_statistic.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hopkins_statistic.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
