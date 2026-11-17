"""Writes vectors/cases/dead_zone.json, stdlib only.

Dead zone (conventions: Dead zone; ADR 0246). The expected values come from the definition
(0 where |x| <= w, x - w above, x + w below) in exact rational arithmetic with binary-fraction
samples and widths, including samples exactly at +-w.

Run from the repo root: python vectors/generators/dead_zone.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def dz(v, w):
    return v - w if v > w else v + w if v < -w else Fr(0)


def add(cid, x, w, why):
    y = [dz(Fr(v), Fr(w)) for v in x]
    cases.append({"id": f"dead_zone.{cid}", "op": "dead_zone",
                  "args": {"samples": x, "width": w}, "expected": [float(v) for v in y],
                  "tol": TOL, "source": why})
    return y


y = add("basic", [-3.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 3.0], 1.0,
        "w = 1: zero inside [-1, 1], shifted by 1 outside")
assert y == [-2, Fr(-1, 2), 0, 0, 0, 0, 0, Fr(1, 2), 2]
y = add("width_zero", [1.5, -2.0, 0.0, 0.25], 0.0, "w = 0: the input itself")
assert y == [Fr(3, 2), -2, 0, Fr(1, 4)]
add("fraction", [0.125, -0.375, 0.625, -0.875, 2.25, -4.5], 0.375, "w = 3/8, samples at -w")
y = add("all_inside", [0.5, -0.25, 0.0], 2.0, "every sample inside the zone")
assert y == [0, 0, 0]


def err(cid, why, **args):
    cases.append({"id": f"dead_zone.{cid}", "op": "dead_zone", "args": args,
                  "error": "invalid_argument", "source": why})


err("width_negative", "width must be at least 0", samples=[1.0], width=-0.5)
err("width_nan", "width must be finite", samples=[1.0], width="nan")
err("empty", "samples must not be empty", samples=[], width=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], width=1.0)

doc = {
    "schema": 1,
    "suite": "dead_zone",
    "description": "Dead zone (conventions: Dead zone; ADR 0246).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dead_zone.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/dead_zone.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
