"""Writes vectors/cases/expander_gain.json, stdlib only.

Downward-expander gain computer (conventions: Downward-expander gain computer; ADR 0256). The
expected gains come from the piecewise definition (0 above the knee, (R - 1) d below, quadratic
in the knee) in exact rationals with dyadic levels and integer ratios.

Run from the repo root: python vectors/generators/expander_gain.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def gain(x, t, r, w):
    d = Fr(x) - Fr(t)
    w = Fr(w)
    s = Fr(r) - 1
    if 2 * d > w:
        return Fr(0)
    if 2 * d < -w:
        return s * d
    if w == 0:
        return Fr(0)
    return -(s * (d - w / 2) ** 2 / (2 * w))


def add(cid, x, t, r, why, w=None):
    y = [gain(v, t, r, w or 0) for v in x]
    args = {"level_db": x, "threshold_db": t, "ratio": r}
    if w is not None:
        args["knee_db"] = w
    cases.append({"id": f"expander_gain.{cid}", "op": "expander_gain", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("hard_knee", [0.0, -40.0, -41.0, -50.0, -60.0], -40.0, 2.0,
        "T = -40, R = 2, hard knee: 0 at and above T, -1 dB per dB below")
assert y == [0, 0, -1, -10, -20]
y = add("soft_knee", [-30.0, -36.0, -38.0, -40.0, -42.0, -44.0, -50.0], -40.0, 3.0,
        "T = -40, R = 3, 8 dB knee: edges at -36 and -44 are in the knee", w=8.0)
assert y[1] == 0 and y[3] == -2 and y[5] == -8 and y[6] == -20
add("fraction", [-10.5, -12.25, -13.0, -20.0], -12.0, 4.0, "R = 4, 2 dB knee", w=2.0)
y = add("ratio_one", [-80.0, -40.0, 0.0], -40.0, 1.0, "R = 1: 0 dB everywhere", w=4.0)
assert y == [0, 0, 0]
for t, r, w in ((-40, 3, 8), (-12, 4, 2)):
    lo, hi = Fr(t) - Fr(w) / 2, Fr(t) + Fr(w) / 2
    assert gain(hi, t, r, w) == 0 and gain(lo, t, r, w) == (Fr(r) - 1) * (lo - t)


def err(cid, why, **args):
    cases.append({"id": f"expander_gain.{cid}", "op": "expander_gain", "args": args,
                  "error": "invalid_argument", "source": why})


err("ratio_below_one", "ratio must be at least 1", level_db=[0.0], threshold_db=-10.0,
    ratio=0.5)
err("knee_negative", "knee_db must be at least 0", level_db=[0.0], threshold_db=-10.0,
    ratio=2.0, knee_db=-1.0)
err("empty", "level_db must not be empty", level_db=[], threshold_db=-10.0, ratio=2.0)
err("nan_level", "level_db must be finite", level_db=["nan"], threshold_db=-10.0, ratio=2.0)

doc = {
    "schema": 1,
    "suite": "expander_gain",
    "description": "Downward-expander gain computer (conventions: Downward-expander gain "
    "computer; ADR 0256).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "expander_gain.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/expander_gain.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
