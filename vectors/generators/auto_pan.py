"""Writes vectors/cases/auto_pan.json, stdlib only.

Auto-panner (conventions: Auto-panner; ADR 0270): the panner at p[n] = depth cos((2 pi rate)
(n / fs)), with the stdlib math.cos and math.sin.

Run from the repo root: python vectors/generators/auto_pan.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def gains(p, law):
    if law == "linear":
        return (1 - p) / 2, (1 + p) / 2
    theta = (p + 1) * (math.pi / 4)
    return math.cos(theta), math.sin(theta)


def add(cid, x, rate, depth, fs, why, law=None):
    w = 2.0 * math.pi * rate
    left, right = [], []
    for n, v in enumerate(x):
        gl, gr = gains(depth * math.cos(w * (n / fs)), law or "constant_power")
        left.append(v * gl)
        right.append(v * gr)
    args = {"samples": x, "rate": rate, "depth": depth, "sample_rate": fs}
    if law is not None:
        args["law"] = law
    cases.append({"id": f"auto_pan.{cid}", "op": "auto_pan", "args": args,
                  "expected": {"left": left, "right": right}, "tol": TOL, "source": why})
    return left, right


ONES = [1.0] * 8
left, right = add("quarter_rate", ONES, 2.0, 1.0, 8.0,
                  "rate fs/4, depth 1: positions 1, 0, -1, 0, ... (right, centre, left)")
assert abs(right[0] - 1) < 1e-15 and abs(left[0]) < 1e-15 and abs(left[2] - 1) < 1e-15
left, right = add("zero_depth", [0.5, -0.25, 1.0], 3.0, 0.0, 48.0, "depth 0: stays at centre")
assert all(abs(v / x - 2 ** -0.5) < 1e-15 for v, x in zip(left, [0.5, -0.25, 1.0]))
add("signal", [0.25, -1.0, 1.5, 2.0, -0.5, 0.75, 0.1, -0.3, 0.9, 1.2], 1.5, 0.6, 20.0,
    "depth 0.6, rate 1.5 Hz at 20 Hz on a signal")
left, right = add("linear", ONES, 2.0, 0.5, 8.0, "linear law: gains (1 -+ p)/2", law="linear")
assert left[0] == 0.25 and right[0] == 0.75


def err(cid, why, **args):
    base = {"samples": [1.0], "rate": 1.0, "depth": 0.5, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"auto_pan.{cid}", "op": "auto_pan", "args": base,
                  "error": "invalid_argument", "source": why})


err("depth_high", "depth must be at most 1", depth=1.5)
err("depth_negative", "depth must be at least 0", depth=-0.1)
err("rate_nan", "rate must be finite", rate="nan")
err("fs_zero", "sample_rate must be positive", sample_rate=0.0)
err("bad_law", "law must be constant_power or linear", law="square")
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "auto_pan",
    "description": "Auto-panner (conventions: Auto-panner; ADR 0270).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "auto_pan.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/auto_pan.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
