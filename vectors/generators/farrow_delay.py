"""Writes vectors/cases/farrow_delay.json, stdlib only.

Farrow variable delay (conventions: Channel, Farrow variable delay; ADR 0226). The expected
values are the Lagrange interpolator in exact rationals, the product form, not the Farrow
expansion: p = n - delays[n], q = p - (N-1)/2, b = floor(q), mu = q - b,
y[n] = sum_j L_j(mu + (N-1)/2) x[b+j], x zero outside. The delays are binary fractions, so every
step is exact. Polynomial inputs of degree <= N are checked to come out as the polynomial at p
wherever all N + 1 samples are inside.

Run from the repo root: python vectors/generators/farrow_delay.py [--check]
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


def farrow(x, delays, n):
    half = Fr(n - 1, 2)
    out = []
    for i, d in enumerate(delays):
        q = i - Fr(d) - half
        b = math.floor(q)
        u = q - b + half
        acc = 0
        for j in range(n + 1):
            if 0 <= b + j < len(x):
                acc += basis(j, u, n) * x[b + j]
        out.append(acc)
    return out


def cx(v):
    if isinstance(v, tuple):
        return complex(float(v[0]), float(v[1]))
    return complex(float(v))


def add(cid, x, delays, n, why, *, poly=None):
    if poly is None and isinstance(x[0], tuple):
        re = farrow([v[0] for v in x], delays, n)
        im = farrow([v[1] for v in x], delays, n)
        out = [complex(float(a), float(b)) for a, b in zip(re, im)]
        samples = {"re": [float(v[0]) for v in x], "im": [float(v[1]) for v in x]}
    else:
        exact = farrow(x, delays, n)
        if poly is not None:
            half = Fr(n - 1, 2)
            checked = 0
            for i, d in enumerate(delays):
                b = math.floor(i - Fr(d) - half)
                if b >= 0 and b + n < len(x):
                    assert exact[i] == poly(i - Fr(d)), (cid, i)
                    checked += 1
            assert checked > 0, cid
        out = [complex(float(v)) for v in exact]
        samples = [float(v) for v in x]
    args = {"samples": samples, "delays": [float(d) for d in delays]}
    if n != 3:
        args["order"] = n
    cases.append({"id": f"farrow_delay.{cid}", "op": "farrow_delay", "args": args,
                  "expected": {"re": [v.real for v in out], "im": [v.imag for v in out]},
                  "tol": TOL, "source": why})
    return out


ramp = [Fr(k) for k in range(1, 9)]
out = add("integer_shift", ramp, [2] * 8, 3, "order 3, delay 2: an exact shift, zeros in front")
assert out == [0, 0, 1, 2, 3, 4, 5, 6]
lin = [Fr(3, 2), Fr(-1), Fr(5, 4), Fr(2), Fr(0), Fr(-3, 4)]
out = add("linear", lin, [Fr(1, 4), Fr(1, 2), Fr(3, 4), Fr(1), Fr(5, 4), Fr(-1, 2)], 1,
          "order 1: (1 - mu) x[b] + mu x[b+1]")
assert out[1] == complex(float(Fr(1, 2) * lin[0] + Fr(1, 2) * lin[1]))


def cubic(t):
    return Fr(1, 64) * t**3 - Fr(1, 4) * t**2 + t - 2


xs = [cubic(Fr(k)) for k in range(14)]
add("cubic_exact", xs, [Fr(k % 5, 4) + Fr(1, 8) for k in range(14)], 3,
    "order 3 on a cubic: exact inside, varying delays", poly=cubic)


def quintic(t):
    return Fr(1, 1000) * t**5 - Fr(1, 50) * t**3 + Fr(1, 3) * t


xs = [quintic(Fr(k)) for k in range(16)]
add("order_five", xs, [Fr(5, 2) - Fr(k, 8) for k in range(16)], 5,
    "order 5 on a quintic: exact inside", poly=quintic)


def quad(t):
    return 2 * t**2 - 3 * t + 1


xs = [quad(Fr(k)) for k in range(10)]
add("order_two", xs, [Fr(3, 2), Fr(1), Fr(7, 8), Fr(1, 4), Fr(2), Fr(5, 2), Fr(-1, 4), Fr(0),
                      Fr(9, 8), Fr(1, 2)], 2,
    "order 2 on a quadratic: exact inside; integer delays interpolate at mu = 1/2", poly=quad)
add("advance_and_far", [Fr(1), Fr(-2), Fr(3), Fr(1, 2), Fr(-1)], [Fr(-3, 4), Fr(-1, 8), Fr(40),
                                                                    Fr(-64), Fr(3, 8)], 3,
    "negative delays advance; delays far past the ends read zeros")
add("complex", [(Fr(1), Fr(1, 2)), (Fr(-1, 4), Fr(2)), (Fr(3, 4), Fr(-1)), (Fr(0), Fr(1, 8)),
                (Fr(5, 4), Fr(1, 4))], [Fr(1, 2), Fr(3, 8), Fr(5, 8), Fr(1), Fr(1, 16)], 3,
    "complex samples: real and imaginary parts interpolate separately")
cases.append({"id": "farrow_delay.empty", "op": "farrow_delay",
              "args": {"samples": [], "delays": []}, "expected": {"re": [], "im": []},
              "tol": TOL, "source": "empty input gives empty output"})


def err(cid, why, **args):
    cases.append({"id": f"farrow_delay.{cid}", "op": "farrow_delay", "args": args,
                  "error": "invalid_argument", "source": why})


err("length_mismatch", "delays must be as long as samples", samples=[1.0, 2.0], delays=[0.5])
err("nan_delay", "delays must be finite", samples=[1.0, 2.0], delays=[0.5, "nan"])
err("inf_delay", "delays must be finite", samples=[1.0], delays=["inf"])
err("order_zero", "order must be at least 1", samples=[1.0], delays=[0.5], order=0)

doc = {
    "schema": 1,
    "suite": "farrow_delay",
    "description": "Farrow variable delay (conventions: Channel, Farrow variable delay;"
    " ADR 0226).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "farrow_delay.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/farrow_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
