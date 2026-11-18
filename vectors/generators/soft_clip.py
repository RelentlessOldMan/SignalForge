"""Writes vectors/cases/soft_clip.json, stdlib only.

Cubic soft clipper (conventions: Cubic soft clipper; ADR 0250). The expected values come from
the definition (x - x^3/3 on [-1, 1], +-2/3 beyond) in exact rationals with binary-fraction
samples, rounded once to double.

Run from the repo root: python vectors/generators/soft_clip.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 4e-16, "rel": 4e-16}
cases = []


def sc(v):
    v = Fr(v)
    if v >= 1:
        return Fr(2, 3)
    if v <= -1:
        return Fr(-2, 3)
    return v - v**3 / 3


def add(cid, x, why):
    y = [sc(v) for v in x]
    cases.append({"id": f"soft_clip.{cid}", "op": "soft_clip", "args": {"samples": x},
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("edges", [-3.0, -1.0, 0.0, 1.0, 1.5, 100.0], "+-1 give +-2/3; beyond is held there")
assert y == [Fr(-2, 3), Fr(-2, 3), 0, Fr(2, 3), Fr(2, 3), Fr(2, 3)]
y = add("cubic", [0.5, -0.5, 0.25, -0.75, 0.125, 0.875], "x - x^3/3 inside [-1, 1]")
assert y[0] == Fr(11, 24) and y[1] == Fr(-11, 24)
add("small", [2.0**-20, -(2.0**-30), 2.0**-10], "near 0 the slope is 1")


def err(cid, why, **args):
    cases.append({"id": f"soft_clip.{cid}", "op": "soft_clip", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[0.5, "nan"])
err("inf_sample", "samples must be finite", samples=["inf"])

doc = {
    "schema": 1,
    "suite": "soft_clip",
    "description": "Cubic soft clipper (conventions: Cubic soft clipper; ADR 0250).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "soft_clip.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/soft_clip.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
