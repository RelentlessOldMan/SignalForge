"""Writes vectors/cases/quantize.json, stdlib only.

Uniform quantizer (conventions: Uniform quantizer; ADR 0247). Steps are binary fractions and
samples multiples of step/4, so x/step is exact and the rounding (half to even) and the
saturation are decided here by hand in exact rationals.

Run from the repo root: python vectors/generators/quantize.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def round_even(r):
    f = math.floor(r)
    d = r - f
    if d > Fr(1, 2) or (d == Fr(1, 2) and f % 2 == 1):
        return f + 1
    return f


def q(v, step, levels):
    k = round_even(Fr(v) / step)
    if levels is not None:
        top = (levels - 1) // 2
        k = max(-top, min(top, k))
    return step * k


def add(cid, x, step, why, levels=None, im=None):
    st = Fr(step)
    for v in x + (im or []):
        assert (Fr(v) / st * 4).denominator == 1
    args = {"samples": x if im is None else {"re": x, "im": im}, "step": step}
    if levels is not None:
        args["levels"] = levels
    re = [float(q(v, st, levels)) for v in x]
    exp = re if im is None else {"re": re, "im": [float(q(v, st, levels)) for v in im]}
    cases.append({"id": f"quantize.{cid}", "op": "quantize", "args": args, "expected": exp,
                  "tol": TOL, "source": why})
    return exp


y = add("ties", [0.5, 1.5, 2.5, -0.5, -1.5, -2.5, 0.25, 0.75, -0.75], 1.0,
        "step 1: halves round to even, quarters to nearest")
assert y == [0.0, 2.0, 2.0, -0.0, -2.0, -2.0, 0.0, 1.0, -1.0]
add("fine_step", [0.1875, -0.3125, 0.0625, 1.0, -0.125, 0.4375], 0.125, "step 1/8")
y = add("saturate", [3.0, 2.0, 1.25, -1.75, -6.0, 0.5], 0.5, "step 1/2, 7 levels: k in [-3, 3]",
        levels=7)
assert y == [1.5, 1.5, 1.0, -1.5, -1.5, 0.5]
y = add("one_level", [0.75, -3.0], 0.5, "1 level: all zero", levels=1)
assert y == [0.0, 0.0]
add("complex", [0.5, 1.25, -2.5], 1.0, "complex: each part separately",
    im=[-1.5, 0.75, 3.5], levels=5)


def err(cid, why, **args):
    cases.append({"id": f"quantize.{cid}", "op": "quantize", "args": args,
                  "error": "invalid_argument", "source": why})


err("step_zero", "step must be positive", samples=[1.0], step=0.0)
err("levels_even", "levels must be odd", samples=[1.0], step=1.0, levels=4)
err("levels_zero", "levels must be at least 1", samples=[1.0], step=1.0, levels=0)
err("empty", "samples must not be empty", samples=[], step=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], step=1.0)

doc = {
    "schema": 1,
    "suite": "quantize",
    "description": "Uniform quantizer (conventions: Uniform quantizer; ADR 0247).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "quantize.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/quantize.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
