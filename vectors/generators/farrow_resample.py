"""Writes vectors/cases/farrow_resample.json, stdlib only.

Farrow resampler (conventions: Channel, Farrow resampler; ADR 0228). Output k reads the input at
t_k = k / ratio (the float division the convention names, taken exactly from there on) while
t_k <= L - 1, through the order-N Lagrange interpolator in exact rationals, the product form:
q = t_k - (N-1)/2, b = floor(q), y = sum_j L_j(q - b + (N-1)/2) x[b+j], x zero outside. Polynomial
inputs of degree <= N are checked to come out as the polynomial at t_k wherever all N + 1 samples
are inside.

Run from the repo root: python vectors/generators/farrow_resample.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def basis(j, u, n):
    v = Fr(1)
    for m in range(n + 1):
        if m != j:
            v *= (u - m) / Fr(j - m)
    return v


def positions(length, ratio):
    out = []
    k = 0
    while length and k / ratio <= length - 1:
        out.append(Fr(k / ratio))
        k += 1
    return out


def read(x, pos, n):
    half = Fr(n - 1, 2)
    out = []
    for t in pos:
        q = t - half
        b = math.floor(q)
        u = q - b + half
        out.append(sum((basis(j, u, n) * x[b + j] for j in range(n + 1) if 0 <= b + j < len(x)),
                       Fr(0)))
    return out


def add(cid, x, ratio, n, why, *, poly=None, cplx=None):
    pos = positions(len(x), ratio)
    re = read(x, pos, n)
    im = read(cplx, pos, n) if cplx is not None else [Fr(0)] * len(re)
    if poly is not None:
        half = Fr(n - 1, 2)
        checked = 0
        for t, v in zip(pos, re):
            b = math.floor(t - half)
            if b >= 0 and b + n < len(x):
                assert v == poly(t), (cid, t)
                checked += 1
        assert checked > 0, cid
    samples = ({"re": [float(v) for v in x], "im": [float(v) for v in cplx]} if cplx is not None
               else [float(v) for v in x])
    args = {"samples": samples, "ratio": ratio}
    if n != 3:
        args["order"] = n
    cases.append({"id": f"farrow_resample.{cid}", "op": "farrow_resample", "args": args,
                  "expected": {"re": [float(v) for v in re], "im": [float(v) for v in im]},
                  "tol": TOL, "source": why})
    return re


xs = [Fr(v) for v in (3, -1, 4, 1, -5, 9, 2, -6)]
assert add("identity", xs, 1.0, 3, "ratio 1, odd order: the input") == xs
assert add("decimate_two", xs, 0.5, 3, "ratio 1/2, odd order: every other sample") == xs[::2]
out = add("interpolate_two", xs, 2.0, 3, "ratio 2: 15 outputs, the even ones the input")
assert len(out) == 15 and out[::2] == xs


def cubic(t):
    return Fr(1, 32) * t**3 - Fr(1, 2) * t**2 + 2 * t - 1


xs = [cubic(Fr(k)) for k in range(12)]
add("cubic_three_quarters", xs, 0.75, 3, "ratio 3/4 on a cubic: exact inside", poly=cubic)
add("cubic_irrational", xs, math.sqrt(2), 3, "ratio sqrt(2) as a double, on a cubic: exact inside",
    poly=cubic)


def line(t):
    return 3 * t - 2


xs = [line(Fr(k)) for k in range(7)]
add("linear", xs, 1.6, 1, "order 1, ratio 1.6 on a line: exact everywhere", poly=line)


def quartic(t):
    return Fr(1, 100) * t**4 - Fr(1, 5) * t**2 + 1


xs = [quartic(Fr(k)) for k in range(12)]
add("order_four", xs, 1.25, 4, "order 4, ratio 5/4 on a quartic: exact inside", poly=quartic)
add("complex", [Fr(1), Fr(-1, 2), Fr(2), Fr(1, 4), Fr(-3, 4)], 1.5, 3,
    "complex samples: parts interpolate separately",
    cplx=[Fr(1, 2), Fr(1), Fr(-1), Fr(0), Fr(3, 2)])
add("single_sample", [Fr(5, 2)], 3.0, 3, "one sample: only t = 0, which reads it")
cases.append({"id": "farrow_resample.empty", "op": "farrow_resample",
              "args": {"samples": [], "ratio": 2.0}, "expected": {"re": [], "im": []},
              "tol": TOL, "source": "empty input gives empty output"})


def err(cid, why, **args):
    cases.append({"id": f"farrow_resample.{cid}", "op": "farrow_resample", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_ratio", "ratio must be at least 1e-6", samples=[1.0, 2.0], ratio=0.0)
err("negative_ratio", "ratio must be at least 1e-6", samples=[1.0, 2.0], ratio=-1.0)
err("huge_ratio", "ratio must be at most 1e6", samples=[1.0, 2.0], ratio=2e6)
err("nan_ratio", "ratio must be finite", samples=[1.0, 2.0], ratio="nan")
err("order_zero", "order must be at least 1", samples=[1.0, 2.0], ratio=1.5, order=0)

doc = {
    "schema": 1,
    "suite": "farrow_resample",
    "description": "Farrow resampler (conventions: Channel, Farrow resampler; ADR 0228).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "farrow_resample.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/farrow_resample.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
