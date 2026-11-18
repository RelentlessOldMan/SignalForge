"""Writes vectors/cases/stereo_width.json, stdlib only.

Stereo width (conventions: Stereo width; ADR 0267). Binary-fraction inputs and widths, computed
in exact rationals, so the expected values are exact doubles.

Run from the repo root: python vectors/generators/stereo_width.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 0.0}
cases = []
L = [1.0, -0.5, 0.25, 3.0, 0.0]
R = [0.5, 0.5, -0.75, 1.0, -2.0]


def add(cid, left, right, width, why):
    a, b, w = [Fr(v) for v in left], [Fr(v) for v in right], Fr(width)
    m = [(p + q) / 2 for p, q in zip(a, b)]
    s = [(p - q) / 2 * w for p, q in zip(a, b)]
    lo = [x + y for x, y in zip(m, s)]
    ro = [x - y for x, y in zip(m, s)]
    cases.append({"id": f"stereo_width.{cid}", "op": "stereo_width",
                  "args": {"left": left, "right": right, "width": width},
                  "expected": {"left": [float(v) for v in lo], "right": [float(v) for v in ro]},
                  "tol": TOL, "source": why})
    return lo, ro


lo, ro = add("unity", L, R, 1.0, "width 1: unchanged")
assert lo == [Fr(v) for v in L] and ro == [Fr(v) for v in R]
lo, ro = add("mono", L, R, 0.0, "width 0: both channels (l + r)/2")
assert lo == ro
add("narrow", L, R, 0.5, "width 1/2: side halved")
lo, ro = add("wide", L, R, 2.0, "width 2: side doubled, l' = (3l - r)/2")
assert lo[0] == Fr(5, 4)


def err(cid, why, **args):
    base = {"left": [1.0], "right": [0.0], "width": 1.0}
    base.update(args)
    cases.append({"id": f"stereo_width.{cid}", "op": "stereo_width", "args": base,
                  "error": "invalid_argument", "source": why})


err("width_negative", "width must be at least 0", width=-0.5)
err("width_inf", "width must be finite", width="inf")
err("lengths", "left and right must have the same length", right=[0.0, 1.0])
err("empty", "left must not be empty", left=[], right=[])
err("nan", "right must be finite", right=["nan"])

doc = {
    "schema": 1,
    "suite": "stereo_width",
    "description": "Stereo width (conventions: Stereo width; ADR 0267).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "stereo_width.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/stereo_width.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
