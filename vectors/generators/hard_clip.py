"""Writes vectors/cases/hard_clip.json, stdlib only.

Hard clipper (conventions: Hard clipper; ADR 0251). Real cases come from the definition (clamp
to [-limit, limit]) with binary-fraction values, so they are exact. Complex cases use 3-4-5
triangles so |x| and limit/|x| are exact rationals; x * limit/|x| is computed in exact rationals
and rounded once.

Run from the repo root: python vectors/generators/hard_clip.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

cases = []


def add_real(cid, x, lim, why):
    y = [min(max(Fr(v), -Fr(lim)), Fr(lim)) for v in x]
    cases.append({"id": f"hard_clip.{cid}", "op": "hard_clip",
                  "args": {"samples": x, "limit": lim}, "expected": [float(v) for v in y],
                  "tol": {"abs": 0.0, "rel": 0.0}, "source": why})
    return y


def add_complex(cid, re, im, mags, lim, why):
    yr, yi = [], []
    for a, b, m in zip(re, im, mags):
        a, b, m, L = Fr(a), Fr(b), Fr(m), Fr(lim)
        assert a * a + b * b == m * m
        s = L / m if m > L else Fr(1)
        yr.append(float(a * s))
        yi.append(float(b * s))
    cases.append({"id": f"hard_clip.{cid}", "op": "hard_clip",
                  "args": {"samples": {"re": re, "im": im}, "limit": lim},
                  "expected": {"re": yr, "im": yi}, "tol": {"abs": 1e-15, "rel": 1e-15},
                  "source": why})
    return yr, yi


y = add_real("basic", [-3.0, -1.0, -0.5, 0.0, 0.75, 1.0, 2.5], 1.0,
             "clamp to [-1, 1]; +-1 pass")
assert y == [-1, -1, Fr(-1, 2), 0, Fr(3, 4), 1, 1]
add_real("fraction", [0.375, -0.625, 0.1875, -0.0625], 0.25, "limit 1/4")
y = add_real("limit_zero", [1.5, -2.0, 0.0], 0.0, "limit 0: all zero")
assert y == [0, 0, 0]
yr, yi = add_complex("complex", [3.0, -6.0, 0.375, 0.0, -1.5], [4.0, 8.0, -0.5, -0.5, 2.0],
                     [5, 10, Fr(5, 8), Fr(1, 2), Fr(5, 2)], 2.0,
                     "3-4-5 triangles: |x| = 5, 10, 5/8, 1/2, 5/2 against limit 2")
assert yr[0] == 1.2 and yi[0] == 1.6 and yr[2] == 0.375 and yi[3] == -0.5


def err(cid, why, **args):
    cases.append({"id": f"hard_clip.{cid}", "op": "hard_clip", "args": args,
                  "error": "invalid_argument", "source": why})


err("limit_negative", "limit must be at least 0", samples=[1.0], limit=-1.0)
err("limit_inf", "limit must be finite", samples=[1.0], limit="inf")
err("empty", "samples must not be empty", samples=[], limit=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], limit=1.0)

doc = {
    "schema": 1,
    "suite": "hard_clip",
    "description": "Hard clipper (conventions: Hard clipper; ADR 0251).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hard_clip.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hard_clip.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
