"""Writes vectors/cases/bray_curtis.json, stdlib only.

The Bray-Curtis dissimilarity (conventions: Bray-Curtis dissimilarity; ADR 0418): exact in
rationals.

Run from the repo root: python vectors/generators/bray_curtis.py [--check]
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
    num = sum(abs(Fr(a) - Fr(b)) for a, b in zip(x, y))
    den = sum(Fr(a) + Fr(b) for a, b in zip(x, y))
    d = num / den
    cases.append(
        {
            "id": f"bray_curtis.{cid}",
            "op": "bray_curtis",
            "args": {"x": x, "y": y},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return d


got = add("same", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "equal vectors: 0")
assert got == 0
got = add("apart", [1.0, 0.0], [0.0, 1.0], "no index where both are positive: 2/2 = 1")
assert got == 1
got = add("mixed", [3.0, 1.0], [1.0, 1.0], "|3 - 1| + 0 over 3 + 1 + 1 + 1: 2/6 = 1/3")
assert got == Fr(1, 3)
got = add("one_empty", [0.0, 0.0], [1.0, 2.0], "x all zero: 3/3 = 1")
assert got == 1
got = add("scaled", [1.0, 2.0], [2.0, 4.0], "y twice x: not normalized, so 3/9 = 1/3")
assert got == Fr(1, 3)
rng = random.Random(418)
x = [rng.randint(0, 20) / 4 for _ in range(16)]
y = [rng.randint(0, 20) / 4 for _ in range(16)]
add("random", x, y, "16 quarters each from random.Random(418), 0 to 5")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"bray_curtis.{cid}",
            "op": "bray_curtis",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "x needs a value", x=[], y=[])
err("lengths", "x and y must match", y=[1.0, 1.0])
err("negative", "values must be non-negative", y=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", x=[1.0, "inf", 1.0])
err("all_zero", "x and y both all zero", x=[0.0, 0.0, 0.0], y=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "bray_curtis",
    "description": "The Bray-Curtis dissimilarity (conventions: Bray-Curtis dissimilarity; "
    "ADR 0418).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bray_curtis.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bray_curtis.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
