"""Writes vectors/cases/fade.json, stdlib only.

Fades (conventions: Fades; ADR 0262). Linear gains come from exact rationals; cosine gains from
(1 - cos(pi t)) / 2 with the stdlib math.cos, checked by hand at t = 0, 1/4, 1/2, 3/4.

Run from the repo root: python vectors/generators/fade.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 0.0}
cases = []


def ramp(k, length, shape):
    if shape == "linear":
        return Fr(k, length)
    return (1 - math.cos(math.pi * (k / length))) / 2


def gains(size, li, lo, shape):
    g = [1 for _ in range(size)]
    for n in range(li):
        g[n] = g[n] * ramp(n, li, shape)
    for k in range(lo):
        g[size - 1 - k] = g[size - 1 - k] * ramp(k, lo, shape)
    return g


def add(cid, x, li, lo, why, shape=None):
    g = gains(len(x), li, lo, shape or "linear")
    args = {"samples": x, "fade_in": li, "fade_out": lo}
    if shape is not None:
        args["shape"] = shape
    cases.append({"id": f"fade.{cid}", "op": "fade", "args": args,
                  "expected": [float(v * k) for v, k in zip(x, g)], "tol": TOL, "source": why})
    return g


g = add("linear", [1.0] * 10, 4, 2, "linear, in 4, out 2: 0, 1/4, 1/2, 3/4, 1, ..., 1, 1/2, 0")
assert g == [0, Fr(1, 4), Fr(1, 2), Fr(3, 4), 1, 1, 1, 1, Fr(1, 2), 0]
g = add("cosine", [2.0] * 8, 4, 4, "cosine, in 4, out 4", shape="cosine")
want = [0, (2 - math.sqrt(2)) / 4, 0.5, (2 + math.sqrt(2)) / 4]
assert all(abs(a - b) < 1e-15 for a, b in zip(g, want + want[::-1]))
g = add("overlap", [1.0, -2.0, 3.0, -4.0], 4, 4, "ramps overlap and multiply")
assert g == [0, Fr(1, 4) * Fr(1, 2), Fr(1, 2) * Fr(1, 4), 0]
g = add("none", [0.5, -0.25, 1.5], 0, 0, "no fades: unchanged", shape="linear")
assert g == [1, 1, 1]
add("signal", [0.25, -1.0, 1.5, 2.0, -0.5, 0.75, 1.0, -1.25, 0.5], 3, 5, "cosine on a signal",
    shape="cosine")

re = [1.0, 2.0, -3.0, 0.5]
im = [0.5, -1.0, 4.0, 0.0]
g = gains(4, 2, 0, "linear")
cases.append({"id": "fade.complex", "op": "fade",
              "args": {"samples": {"re": re, "im": im}, "fade_in": 2, "fade_out": 0},
              "expected": {"re": [float(v * k) for v, k in zip(re, g)],
                           "im": [float(v * k) for v, k in zip(im, g)]},
              "tol": TOL, "source": "complex scaled part by part, gains 0, 1/2, 1, 1"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "fade_in": 1, "fade_out": 1}
    base.update(args)
    cases.append({"id": f"fade.{cid}", "op": "fade", "args": base,
                  "error": "invalid_argument", "source": why})


err("fade_in_negative", "fade_in must be at least 0", fade_in=-1)
err("fade_out_too_long", "fade_out must be at most the number of samples", fade_out=3)
err("bad_shape", "shape must be linear or cosine", shape="square")
err("empty", "samples must not be empty", samples=[], fade_in=0, fade_out=0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "fade",
    "description": "Fades (conventions: Fades; ADR 0262).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fade.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fade.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
