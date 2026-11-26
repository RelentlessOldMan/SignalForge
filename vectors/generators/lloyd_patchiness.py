"""Writes vectors/cases/lloyd_patchiness.json, stdlib only.

Lloyd's index of patchiness (conventions: Lloyd's index of patchiness; ADR 0610): the mean
crowding sum(x (x - 1))/sum(x) over the mean sum(x)/n, with fractions.

Run from the repo root: python vectors/generators/lloyd_patchiness.py [--check]
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
    f = (sum(c * (c - 1) for c in xs) / sum(xs)) / (sum(xs) / len(xs))
    cases.append(
        {
            "id": f"lloyd_patchiness.{cid}",
            "op": "lloyd_patchiness",
            "args": {"counts": counts},
            "expected": float(f) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add("even", [2.0, 2.0, 2.0], "mean crowding 1 over mean 2: 1/2") == Fr(1, 2)
assert add("one_unit", [5.0], "mean crowding 4 over mean 5: 4/5") == Fr(4, 5)
assert add("singles", [1.0, 1.0, 1.0, 0.0], "no two share a unit: 0") == 0
assert add("clumped", [0.0, 0.0, 6.0], "mean crowding 5 over mean 2: 5/2") == Fr(5, 2)
assert add("mixed", [1.0, 2.0, 3.0], "mean crowding 4/3 over mean 2: 2/3") == Fr(2, 3)
assert add(
    "uneven", [4.0, 0.0, 1.0, 0.0, 3.0], "mean crowding 9/4 over mean 8/5: 45/32"
) == Fr(45, 32)
assert add(
    "huge", [1e308, 1e308], "the sums would overflow: (t - 1)/t, 1 to double precision"
) == 1 - 1 / Fr(1e308)
assert add(
    "many_singles",
    [1.0] * 1000 + [3.0],
    "1000 ones and a 3: sum x(x - 1) 6, total 1003, n 1001: (6/1003)/(1003/1001)",
) == Fr(6 * 1001, 1003**2)
cases[-1]["tol"] = {
    "abs": 0.0,
    "rel": 1e-13,
}  # a small value: hold it to relative accuracy
rng = random.Random(610)
counts = [float(rng.choice([0, 0, 1, 2, 3, 7])) for _ in range(30)]
add("random", counts, "30 counts from random.Random(610).choice([0, 0, 1, 2, 3, 7])")


def err(cid, why, counts):
    cases.append(
        {
            "id": f"lloyd_patchiness.{cid}",
            "op": "lloyd_patchiness",
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
    "suite": "lloyd_patchiness",
    "description": "Lloyd's index of patchiness (conventions: Lloyd's index of patchiness; "
    "ADR 0610).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lloyd_patchiness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/lloyd_patchiness.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
