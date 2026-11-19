"""Writes vectors/cases/wasserstein_distance.json, stdlib only.

The first Wasserstein distance (conventions: first Wasserstein distance; ADR 0403): the area
between the empirical distribution functions, exact in rationals.

Run from the repo root: python vectors/generators/wasserstein_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, x, y, why):
    t = sorted(set(Fr(v) for v in x + y))
    area = Fr(0)
    for a, b in zip(t, t[1:]):
        fx = Fr(sum(Fr(v) <= a for v in x), len(x))
        fy = Fr(sum(Fr(v) <= a for v in y), len(y))
        area += abs(fx - fy) * (b - a)
    cases.append(
        {
            "id": f"wasserstein_distance.{cid}",
            "op": "wasserstein_distance",
            "args": {"x": x, "y": y},
            "expected": float(area),
            "tol": TOL,
            "source": why,
        }
    )
    return area


got = add("shift", [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], "every value moved by 3: 3")
assert got == 3
got = add("same", [3.0, 1.0, 2.0], [2.0, 3.0, 1.0], "the same values: 0")
assert got == 0
got = add("one_each", [-2.5], [4.0], "one value each: the distance 6.5")
assert got == Fr(13, 2)
got = add(
    "hand",
    [0.0, 0.0, 0.0, 0.0],
    [-1.0, 0.0, 1.0],
    "|F_x - F_y| is 1/3 on [-1, 0) and 1/3 on [0, 1): 2/3",
)
assert got == Fr(2, 3)
got = add(
    "unequal", [0.0, 2.0], [1.0], "1/2 on [0, 1) and 1/2 on [1, 2): 1, the mean distance moved"
)
assert got == 1
rng = random.Random(403)
x = [rng.gauss(0.3, 1.0) for _ in range(40)]
y = [rng.gauss(0.0, 2.0) for _ in range(55)]
add("gaussian", x, y, "40 and 55 values from random.Random(403), N(0.3, 1) and N(0, 2)")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"wasserstein_distance.{cid}",
            "op": "wasserstein_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", x=[1.0, "inf"])

doc = {
    "schema": 1,
    "suite": "wasserstein_distance",
    "description": "The first Wasserstein distance (conventions: first Wasserstein distance; "
    "ADR 0403).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "wasserstein_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/wasserstein_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
