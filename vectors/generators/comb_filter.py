"""Writes vectors/cases/comb_filter.json, stdlib only.

Comb filter (conventions: Comb filter; ADR 0237). Feedforward cases come from the definition;
feedback cases from the impulse response h[kD] = g^k, y[n] = sum_k g^k x[n - kD], without the
recursion. Both in exact rational arithmetic with binary-fraction gains.

Run from the repo root: python vectors/generators/comb_filter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def ff(x, d, g):
    return [x[n] + (g * x[n - d] if n >= d else 0) for n in range(len(x))]


def fb(x, d, g):
    return [sum(g**k * x[n - k * d] for k in range(n // d + 1)) for n in range(len(x))]


def add(cid, x, d, g, why, feedback=False, im=None):
    g = Fr(g)
    f = fb if feedback else ff
    re = f([Fr(v) for v in x], d, g)
    args = {"samples": [float(v) for v in x] if im is None else {"re": x, "im": im}, "delay": d,
            "gain": float(g)}
    if feedback:
        args["feedback"] = True
    if im is None:
        expected = [float(v) for v in re]
    else:
        expected = {"re": [float(v) for v in re], "im": [float(v) for v in f([Fr(v) for v in im], d, g)]}
    cases.append({"id": f"comb_filter.{cid}", "op": "comb_filter", "args": args,
                  "expected": expected, "tol": TOL, "source": why})
    return re


y = add("ff_impulse", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], 3, -0.5, "feedforward impulse: 1 at 0, g at D")
assert y == [1, 0, 0, Fr(-1, 2), 0, 0]
y = add("fb_impulse", [1.0] + [0.0] * 9, 3, 0.5, "feedback impulse: g^k at kD", feedback=True)
assert y == [1, 0, 0, Fr(1, 2), 0, 0, Fr(1, 4), 0, 0, Fr(1, 8)]
add("ff_mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0], 2, 0.75, "feedforward, D = 2")
add("fb_mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 3, -0.875,
    "feedback, D = 3, g = -7/8", feedback=True)
add("ff_large_gain", [1.0, 2.0, 3.0, 4.0], 1, 2.5, "feedforward accepts any finite gain")
add("delay_longer", [1.0, 2.0, 3.0], 5, 0.5, "delay longer than the input: unchanged",
    feedback=True)
add("complex_fb", [1.0, 0.0, -1.0, 2.0, 0.5, 0.25], 2, 0.625, "complex samples, feedback",
    feedback=True, im=[0.0, 1.0, 1.0, -0.5, 0.25, 0.0])


def err(cid, why, **args):
    cases.append({"id": f"comb_filter.{cid}", "op": "comb_filter", "args": args,
                  "error": "invalid_argument", "source": why})


err("delay_zero", "delay must be at least 1", samples=[1.0], delay=0, gain=0.5)
err("fb_unstable", "feedback needs |gain| < 1", samples=[1.0], delay=1, gain=1.0, feedback=True)
err("empty", "samples must not be empty", samples=[], delay=1, gain=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], delay=1, gain=0.5)

doc = {
    "schema": 1,
    "suite": "comb_filter",
    "description": "Comb filter (conventions: Comb filter; ADR 0237).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "comb_filter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/comb_filter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
