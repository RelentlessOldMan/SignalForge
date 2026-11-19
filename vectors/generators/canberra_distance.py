"""Writes vectors/cases/canberra_distance.json, stdlib only.

The Canberra distance (conventions: Canberra distance; ADR 0417): exact in rationals.

Run from the repo root: python vectors/generators/canberra_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    d = Fr(0)
    for a, b in zip(x, y):
        if a == 0 and b == 0:
            continue
        d += abs(Fr(a) - Fr(b)) / (abs(Fr(a)) + abs(Fr(b)))
    cases.append(
        {
            "id": f"canberra_distance.{cid}",
            "op": "canberra_distance",
            "args": {"x": x, "y": y},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return d


got = add("same", [1.0, -2.0, 3.0], [1.0, -2.0, 3.0], "equal vectors: 0")
assert got == 0
got = add("apart", [1.0, 0.0], [0.0, 1.0], "each coordinate zero in one: 1 each, 2")
assert got == 2
got = add("signs", [1.0, -1.0], [-1.0, 1.0], "opposite signs: 2/2 each, 2")
assert got == 2
got = add("mixed", [1.0, 3.0], [2.0, 1.0], "1/3 + 2/4 = 5/6")
assert got == Fr(5, 6)
got = add("shared_zero", [0.0, 1.0], [0.0, 3.0], "index 0 zero in both, dropped: 2/4 = 1/2")
assert got == Fr(1, 2)
got = add(
    "scale",
    [1000.0, 0.001],
    [2000.0, 0.002],
    "each coordinate doubled: 1/3 + 1/3 = 2/3 whatever its size",
)
assert abs(got - Fr(2, 3)) < Fr(1, 10**15)
rng = random.Random(417)
x = [rng.randint(-20, 20) / 4 for _ in range(16)]
y = [rng.randint(-20, 20) / 4 for _ in range(16)]
add("random", x, y, "16 quarters each from random.Random(417), -5 to 5")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"canberra_distance.{cid}",
            "op": "canberra_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "x needs a value", x=[], y=[])
err("lengths", "x and y must match", y=[1.0, 1.0])
err("not_finite", "values must be finite", x=[1.0, "inf", 1.0])
err("nan", "values must be finite", y=[1.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "canberra_distance",
    "description": "The Canberra distance (conventions: Canberra distance; ADR 0417).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "canberra_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/canberra_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
