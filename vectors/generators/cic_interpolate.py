"""Writes vectors/cases/cic_interpolate.json, stdlib only.

CIC interpolator (conventions: CIC interpolator; ADR 0230). The expected values come from
running the hardware structure in exact arithmetic: N combs of delay M at the low rate, R - 1
zeros after each sample, then N integrators at the high rate. They are cross-checked against the
FIR form, the zero-stuffed input convolved with the CIC taps (the polynomial
((1 - z^-RM) / (1 - z^-1))^N expanded with Python integers).

Run from the repo root: python vectors/generators/cic_interpolate.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-9, "rel": 1e-13}
cases = []


def taps(r, n, m):
    h = [1]
    for _ in range(n):
        nxt = [0] * (len(h) + r * m - 1)
        for i, v in enumerate(h):
            for j in range(r * m):
                nxt[i + j] += v
        h = nxt
    assert sum(h) == (r * m) ** n
    return h


def hardware(x, r, n, m):
    s = list(x)
    for _ in range(n):
        s = [v - (s[k - m] if k >= m else 0) for k, v in enumerate(s)]
    u = []
    for v in s:
        u += [v] + [0] * (r - 1)
    for _ in range(n):
        acc = 0
        out = []
        for v in u:
            acc += v
            out.append(acc)
        u = out
    return u


def fir(x, r, n, m):
    h = taps(r, n, m)
    u = []
    for v in x:
        u += [v] + [0] * (r - 1)
    return [sum(h[j] * u[k - j] for j in range(len(h)) if k - j >= 0) for k in range(len(u))]


def add(cid, x, r, n, m, why, cplx=None):
    re = hardware(x, r, n, m)
    assert re == fir(x, r, n, m), cid
    im = hardware(cplx, r, n, m) if cplx is not None else None
    if cplx is not None:
        assert im == fir(cplx, r, n, m), cid
    samples = ({"re": [float(v) for v in x], "im": [float(v) for v in cplx]} if cplx is not None
               else [float(v) for v in x])
    args = {"samples": samples, "factor": r, "stages": n}
    if m != 1:
        args["delay"] = m
    expected = ({"re": [float(v) for v in re], "im": [float(v) for v in im]} if cplx is not None
                else [float(v) for v in re])
    cases.append({"id": f"cic_interpolate.{cid}", "op": "cic_interpolate", "args": args,
                  "expected": expected, "tol": TOL, "source": why})
    return re


out = add("dc", [1] * 8, 4, 3, 1, "all ones: settles to (RM)^N / R = 16")
assert out[-1] == 16
out = add("impulse", [1, 0, 0, 0, 0], 2, 3, 1, "impulse: the taps, then zeros")
h = taps(2, 3, 1)
assert out == h + [0] * (10 - len(h))
add("integers", [3, -1, 4, 1, -5, 9, 2, -6], 3, 2, 2, "integer data, R = 3, N = 2, M = 2: exact")
add("fractions", [Fr(1, 2), Fr(-3, 4), Fr(5, 8), Fr(1, 16)], 2, 4, 1, "binary fractions, R = 2, N = 4")
add("factor_one", [2, -1, 3, 0, 1], 1, 2, 3, "R = 1, M = 3: plain filtering")
add("single_sample", [5], 3, 2, 1, "one sample: the first R taps")
add("complex", [1, -2, 3, 1], 2, 2, 1, "complex samples", cplx=[0, 1, -1, 2])


def err(cid, why, **args):
    cases.append({"id": f"cic_interpolate.{cid}", "op": "cic_interpolate", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "samples must not be empty", samples=[], factor=2, stages=2)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], factor=2, stages=2)
err("stages_zero", "stages must be at least 1", samples=[1.0], factor=2, stages=0)
err("gain_too_big", "(RM)^N over 2^53", samples=[1.0], factor=1000, stages=6)

doc = {
    "schema": 1,
    "suite": "cic_interpolate",
    "description": "CIC interpolator (conventions: CIC interpolator; ADR 0230).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cic_interpolate.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cic_interpolate.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
