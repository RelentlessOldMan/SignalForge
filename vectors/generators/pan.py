"""Writes vectors/cases/pan.json, stdlib only.

Panner (conventions: Panner; ADR 0265). Linear gains are exact rationals; constant-power gains
use the stdlib math.cos and math.sin, an independent implementation.

Run from the repo root: python vectors/generators/pan.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []
X = [1.0, -0.5, 0.25, 2.0]


def add(cid, x, position, why, law=None):
    if law == "linear":
        gl, gr = (1 - Fr(position)) / 2, (1 + Fr(position)) / 2
        left = [float(Fr(v) * gl) for v in x]
        right = [float(Fr(v) * gr) for v in x]
    else:
        theta = (position + 1) * (math.pi / 4)
        gl, gr = math.cos(theta), math.sin(theta)
        left = [v * gl for v in x]
        right = [v * gr for v in x]
    args = {"samples": x, "position": position}
    if law is not None:
        args["law"] = law
    cases.append({"id": f"pan.{cid}", "op": "pan", "args": args,
                  "expected": {"left": left, "right": right}, "tol": TOL, "source": why})
    return left, right


left, right = add("centre", X, 0.0, "constant power, centre: both gains cos(pi/4) = 1/sqrt 2")
assert abs(left[0] - 2 ** -0.5) < 1e-16 and abs(right[0] - 2 ** -0.5) < 1e-16
left, right = add("hard_left", X, -1.0, "constant power, -1: left gain 1, right gain 0")
assert left == X and right == [0.0] * 4
add("hard_right", X, 1.0, "constant power, 1: right gain 1, left gain cos(pi/2)")
add("quarter", X, 0.5, "constant power, 0.5: theta = 3 pi/8", law="constant_power")
left, right = add("linear_centre", X, 0.0, "linear, centre: both gains 1/2", law="linear")
assert left == [v / 2 for v in X] == right
add("linear_left", X, -0.5, "linear, -0.5: gains 3/4 and 1/4", law="linear")


def err(cid, why, **args):
    base = {"samples": [1.0], "position": 0.0}
    base.update(args)
    cases.append({"id": f"pan.{cid}", "op": "pan", "args": base,
                  "error": "invalid_argument", "source": why})


err("position_high", "position must be at most 1", position=1.5)
err("position_nan", "position must be finite", position="nan")
err("bad_law", "law must be constant_power or linear", law="square")
err("empty", "samples must not be empty", samples=[])
err("inf_sample", "samples must be finite", samples=["inf"])

doc = {
    "schema": 1,
    "suite": "pan",
    "description": "Panner (conventions: Panner; ADR 0265).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pan.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pan.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
