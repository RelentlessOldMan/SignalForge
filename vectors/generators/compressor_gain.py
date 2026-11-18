"""Writes vectors/cases/compressor_gain.json, stdlib only.

Compressor gain computer (conventions: Compressor gain computer; ADR 0254). The expected gains
come from the piecewise definition (0 below the knee, (1/R - 1) d above, quadratic in the knee)
in exact rationals with dyadic levels, thresholds and knee widths.

Run from the repo root: python vectors/generators/compressor_gain.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

cases = []


def gain(x, t, r, w):
    d = Fr(x) - Fr(t)
    w = Fr(w)
    s = 1 / Fr(r) - 1
    if 2 * d < -w:
        return Fr(0)
    if 2 * d > w:
        return s * d
    if w == 0:
        return Fr(0)
    return s * (d + w / 2) ** 2 / (2 * w)


def add(cid, x, t, r, why, w=None, tol=0.0):
    y = [gain(v, t, r, w or 0) for v in x]
    args = {"level_db": x, "threshold_db": t, "ratio": r}
    if w is not None:
        args["knee_db"] = w
    cases.append({"id": f"compressor_gain.{cid}", "op": "compressor_gain", "args": args,
                  "expected": [float(v) for v in y], "tol": {"abs": tol, "rel": tol},
                  "source": why})
    return y


y = add("hard_knee", [-40.0, -20.0, -19.0, -10.0, 0.0], -20.0, 4.0,
        "T = -20, R = 4, hard knee: 0 at and below T, -3/4 dB per dB above")
assert y == [0, 0, Fr(-3, 4), Fr(-15, 2), -15]
y = add("soft_knee", [-30.0, -24.0, -22.0, -20.0, -18.0, -16.0, -10.0], -20.0, 4.0,
        "T = -20, R = 4, 8 dB knee: edges at -24 and -16 are in the knee", w=8.0)
assert y[1] == 0 and y[3] == Fr(-3, 4) and y[5] == -3 and y[6] == Fr(-15, 2)
add("ratio_two", [-6.5, -3.0, 0.0, 6.25], -3.0, 2.0, "R = 2, 2 dB knee", w=2.0)
add("ratio_three", [-12.0, -9.0, -5.0, 0.0], -10.0, 3.0, "R = 3: 1/R - 1 rounds", w=4.0,
    tol=1e-14)
y = add("ratio_one", [-50.0, 0.0, 20.0], -10.0, 1.0, "R = 1: 0 dB everywhere", w=6.0)
assert y == [0, 0, 0]
# Continuity at both knee edges, and of the slope.
for t, r, w in ((-20, 4, 8), (-3, 2, 2), (-10, 3, 4)):
    lo, hi = Fr(t) - Fr(w) / 2, Fr(t) + Fr(w) / 2
    s = 1 / Fr(r) - 1
    assert gain(lo, t, r, w) == 0 and gain(hi, t, r, w) == s * (hi - t)


def err(cid, why, **args):
    cases.append({"id": f"compressor_gain.{cid}", "op": "compressor_gain", "args": args,
                  "error": "invalid_argument", "source": why})


err("ratio_below_one", "ratio must be at least 1", level_db=[0.0], threshold_db=-10.0,
    ratio=0.5)
err("knee_negative", "knee_db must be at least 0", level_db=[0.0], threshold_db=-10.0,
    ratio=2.0, knee_db=-1.0)
err("threshold_nan", "threshold_db must be finite", level_db=[0.0], threshold_db="nan",
    ratio=2.0)
err("empty", "level_db must not be empty", level_db=[], threshold_db=-10.0, ratio=2.0)
err("nan_level", "level_db must be finite", level_db=[0.0, "nan"], threshold_db=-10.0,
    ratio=2.0)

doc = {
    "schema": 1,
    "suite": "compressor_gain",
    "description": "Compressor gain computer (conventions: Compressor gain computer; ADR 0254).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "compressor_gain.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/compressor_gain.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
