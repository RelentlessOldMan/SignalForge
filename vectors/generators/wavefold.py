"""Writes vectors/cases/wavefold.json, stdlib only.

Wavefolder (conventions: Wavefolder; ADR 0252). The expected values come from repeated
reflection about +-L in exact rationals (a different route from the closed-form triangle the
code uses), with binary-fraction samples and limits.

Run from the repo root: python vectors/generators/wavefold.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def fold(v, lim):
    v, lim = Fr(v), Fr(lim)
    while v > lim or v < -lim:
        v = 2 * lim - v if v > lim else -2 * lim - v
    return v


def add(cid, x, lim, why):
    y = [fold(v, lim) for v in x]
    cases.append({"id": f"wavefold.{cid}", "op": "wavefold", "args": {"samples": x, "limit": lim},
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("one_fold", [0.0, 0.5, 1.0, 1.25, 1.5, 2.0, -1.0, -1.75], 1.0,
        "L = 1: inside unchanged, 1 + d -> 1 - d")
assert y == [0, Fr(1, 2), 1, Fr(3, 4), Fr(1, 2), 0, -1, Fr(-1, 4)]
y = add("many_folds", [3.0, 4.0, 5.5, -6.25, 9.0, -13.0], 1.0, "several reflections")
assert y == [-1, 0, Fr(1, 2), Fr(1, 4), 1, -1]
add("limit_fraction", [0.375, 0.875, -1.125, 2.0, -3.5], 0.75, "L = 3/4")


def err(cid, why, **args):
    cases.append({"id": f"wavefold.{cid}", "op": "wavefold", "args": args,
                  "error": "invalid_argument", "source": why})


err("limit_zero", "limit must be positive", samples=[1.0], limit=0.0)
err("limit_inf", "limit must be finite", samples=[1.0], limit="inf")
err("empty", "samples must not be empty", samples=[], limit=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], limit=1.0)

doc = {
    "schema": 1,
    "suite": "wavefold",
    "description": "Wavefolder (conventions: Wavefolder; ADR 0252).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "wavefold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/wavefold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
