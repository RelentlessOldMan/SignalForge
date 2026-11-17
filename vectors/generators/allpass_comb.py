"""Writes vectors/cases/allpass_comb.json, stdlib only.

Schroeder allpass section (conventions: Schroeder allpass section; ADR 0240). The expected values
convolve the input with the impulse response h[0] = -g, h[kD] = (1 - g^2) g^(k-1), in exact
rational arithmetic with binary-fraction gains, without the recursion.

Run from the repo root: python vectors/generators/allpass_comb.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def h(k, d, g):
    if k == 0:
        return -g
    if k % d:
        return Fr(0)
    return (1 - g * g) * g ** (k // d - 1)


def ap(x, d, g):
    return [sum(h(k, d, g) * x[n - k] for k in range(n + 1)) for n in range(len(x))]


def add(cid, x, d, g, why, im=None):
    g = Fr(g)
    re = ap([Fr(v) for v in x], d, g)
    args = {"samples": [float(v) for v in x] if im is None else {"re": x, "im": im}, "delay": d,
            "gain": float(g)}
    if im is None:
        expected = [float(v) for v in re]
    else:
        expected = {"re": [float(v) for v in re], "im": [float(v) for v in ap([Fr(v) for v in im], d, g)]}
    cases.append({"id": f"allpass_comb.{cid}", "op": "allpass_comb", "args": args,
                  "expected": expected, "tol": TOL, "source": why})
    return re


y = add("impulse", [1.0] + [0.0] * 9, 3, 0.5, "impulse: -g at 0, (1 - g^2) g^(k-1) at kD")
assert y == [Fr(-1, 2), 0, 0, Fr(3, 4), 0, 0, Fr(3, 8), 0, 0, Fr(3, 16)]
assert sum(v * v for v in ap([Fr(1)] + [Fr(0)] * 199, 1, Fr(1, 2))) > 1 - Fr(1, 10**50)
y = add("impulse_negative", [1.0] + [0.0] * 6, 2, -0.75, "impulse with g = -3/4")
assert y == [Fr(3, 4), 0, Fr(7, 16), 0, Fr(-21, 64), 0, Fr(63, 256)]
add("mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 3, 0.625, "mixed, D = 3")
add("delay_one", [1.0, -2.0, 0.5, 0.0, 4.0, -1.0], 1, -0.375, "D = 1: first-order allpass")
y = add("gain_zero", [1.0, 2.0, 3.0, 4.0, 5.0], 2, 0.0, "g = 0: a pure delay of D")
assert y == [0, 0, 1, 2, 3]
add("delay_longer", [1.0, 2.0, 3.0], 5, 0.5, "delay longer than the input: -g x")
add("complex", [1.0, 0.0, -1.0, 2.0, 0.5, 0.25], 2, 0.75, "complex samples",
    im=[0.0, 1.0, 1.0, -0.5, 0.25, 0.0])


def err(cid, why, **args):
    cases.append({"id": f"allpass_comb.{cid}", "op": "allpass_comb", "args": args,
                  "error": "invalid_argument", "source": why})


err("delay_zero", "delay must be at least 1", samples=[1.0], delay=0, gain=0.5)
err("gain_one", "gain needs |g| < 1", samples=[1.0], delay=1, gain=-1.0)
err("empty", "samples must not be empty", samples=[], delay=1, gain=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], delay=1, gain=0.5)

doc = {
    "schema": 1,
    "suite": "allpass_comb",
    "description": "Schroeder allpass section (conventions: Schroeder allpass section; ADR 0240).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "allpass_comb.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/allpass_comb.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
