"""Writes vectors/cases/chebyshev_distance.json, stdlib only.

The Chebyshev distance (conventions: Chebyshev distance; ADR 0420): exact in rationals.

Run from the repo root: python vectors/generators/chebyshev_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 1e-15}
cases = []


def add(cid, x, y, why):
    d = max(abs(Fr(a) - Fr(b)) for a, b in zip(x, y))
    cases.append(
        {
            "id": f"chebyshev_distance.{cid}",
            "op": "chebyshev_distance",
            "args": {"x": x, "y": y},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return d


got = add("same", [1.0, -2.0], [1.0, -2.0], "equal vectors: 0")
assert got == 0
got = add("triangle", [0.0, 0.0], [3.0, 4.0], "the 3-4-5 triangle: the larger side, 4")
assert got == 4
got = add("signs", [1.0, -5.0, 2.0], [-1.0, 1.0, 2.0], "differences 2, 6, 0: 6")
assert got == 6
got = add("huge", [1e300, -1e300], [-1e300, 0.0], "differences 2e300 and 1e300: 2e300")
assert got == 2 * Fr(1e300)
got = add("one", [0.5], [-0.25], "one coordinate: 3/4")
assert got == Fr(3, 4)
rng = random.Random(420)
x = [rng.randint(-20, 20) / 4 for _ in range(16)]
y = [rng.randint(-20, 20) / 4 for _ in range(16)]
add("random", x, y, "16 quarters each from random.Random(420), -5 to 5")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"chebyshev_distance.{cid}",
            "op": "chebyshev_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "x needs a value", x=[], y=[])
err("lengths", "x and y must match", y=[1.0, 1.0])
err("not_finite", "values must be finite", y=[1.0, "-inf", 1.0])
err("overflow", "the difference 1e308 - (-1e308) overflows", x=[1e308], y=[-1e308])

doc = {
    "schema": 1,
    "suite": "chebyshev_distance",
    "description": "The Chebyshev distance (conventions: Chebyshev distance; ADR 0420).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chebyshev_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chebyshev_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
