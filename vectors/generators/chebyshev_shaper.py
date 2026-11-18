"""Writes vectors/cases/chebyshev_shaper.json, stdlib only.

Chebyshev waveshaper (conventions: Chebyshev waveshaper; ADR 0321), from the definition, not
Clenshaw's order: T_0 = 1, T_1 = x, T_{k+1} = 2 x T_k - T_{k-1}; y = sum_k w_k T_k(x) in exact
rationals, rounded once.

Run from the repo root: python vectors/generators/chebyshev_shaper.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def shape(x, w):
    x = Fr(x)
    t = [Fr(1), x]
    while len(t) < len(w):
        t.append(2 * x * t[-1] - t[-2])
    return float(sum(Fr(wk) * tk for wk, tk in zip(w, t)))


def add(cid, x, w, why):
    y = [shape(v, w) for v in x]
    cases.append({"id": f"chebyshev_shaper.{cid}", "op": "chebyshev_shaper",
                  "args": {"samples": x, "weights": w}, "expected": y, "tol": TOL,
                  "source": why})
    return y


xs = [-1.0, -0.75, -0.5, -0.125, 0.0, 0.3, 0.5, 0.875, 1.0]
y = add("third", xs, [0.0, 0.0, 0.0, 1.0], "T_3 = 4x^3 - 3x alone")
assert y[0] == -1.0 and y[2] == 1.0 and y[-1] == 1.0, y
add("mix", xs, [0.1, 1.0, 0.5, -0.25, 0.125], "a mix of T_0 .. T_4")
add("tenth", [-0.9, -0.2, 0.05, 0.7, 0.99], [0.0] * 10 + [1.0], "T_10 alone, ten steps")
add("constant", [0.25, -0.5], [0.75], "one weight: y = w_0")
# cos(2 pi n / 8) at the dyadic points: cos(0) = 1, cos(pi/2) = 0, cos(pi) = -1
y = add("harmonic", [1.0, 0.0, -1.0, 0.0], [0.0, 0.0, 1.0], "T_2(cos t) = cos 2t at t = 0, "
        "pi/2, pi, 3pi/2: 1, -1, 1, -1")
assert y == [1.0, -1.0, 1.0, -1.0], y


def err(cid, why, **args):
    base = {"samples": [0.5, -0.5], "weights": [0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"chebyshev_shaper.{cid}", "op": "chebyshev_shaper", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_one", "samples must be within [-1, 1]", samples=[0.5, 1.0000001])
err("no_weights", "weights must not be empty", weights=[])
err("no_samples", "samples must not be empty", samples=[])
err("weight_nan", "weights must be finite", weights=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "chebyshev_shaper",
    "description": "Chebyshev waveshaper (conventions: Chebyshev waveshaper; ADR 0321).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chebyshev_shaper.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chebyshev_shaper.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
