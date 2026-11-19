"""Writes vectors/cases/glass_delta.json, stdlib only.

Glass's delta (conventions: Glass's delta; ADR 0399): the means and the control's sum of
squares exact in rationals, the root in 40-digit decimal.

Run from the repo root: python vectors/generators/glass_delta.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
decimal.getcontext().prec = 40
D = decimal.Decimal
cases = []


def add(cid, x, y, why):
    fx, fy = [Fr(v) for v in x], [Fr(v) for v in y]
    mx, my = sum(fx) / len(fx), sum(fy) / len(fy)
    var = sum((v - my) ** 2 for v in fy) / (len(fy) - 1)
    delta = D((mx - my).numerator) / D((mx - my).denominator)
    delta /= (D(var.numerator) / D(var.denominator)).sqrt()
    cases.append(
        {
            "id": f"glass_delta.{cid}",
            "op": "glass_delta",
            "args": {"x": x, "y": y},
            "expected": float(delta),
            "tol": TOL,
            "source": why,
        }
    )
    return mx - my, var


got = add("two", [10.0, 20.0, 30.0], [2.0, 4.0, 6.0], "means 20 and 4, s_y^2 = 8/2 = 4: 16/2 = 8")
assert got == (16, 4)
got = add("negative", [0.0], [1.0, 3.0], "x = 0 against mean 2, s_y^2 = 2: -2/sqrt 2 = -sqrt 2")
assert got == (-2, 2)
got = add(
    "swapped", [2.0, 4.0, 6.0], [10.0, 20.0, 30.0], "means 4 and 20, s_y^2 = 200/2 = 100: -16/10"
)
assert got == (-16, 100)
rng = random.Random(399)
x = [rng.gauss(11.0, 3.0) for _ in range(30)]
y = [rng.gauss(10.0, 2.0) for _ in range(50)]
add("gaussian", x, y, "30 and 50 values from random.Random(399), N(11, 3) and N(10, 2)")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"glass_delta.{cid}",
            "op": "glass_delta",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_too_short", "the control needs 2 values", y=[2.0])
err("not_finite", "values must be finite", x=[1.0, "-inf"])
err("no_spread", "s_y = 0", y=[5.0, 5.0, 5.0])

doc = {
    "schema": 1,
    "suite": "glass_delta",
    "description": "Glass's delta (conventions: Glass's delta; ADR 0399).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "glass_delta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/glass_delta.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
