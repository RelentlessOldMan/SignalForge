"""Writes vectors/cases/polyblep_triangle.json, stdlib only.

PolyBLEP triangle (conventions: PolyBLEP triangle; ADR 0314), from the rule in exact rationals:
u = frac(f n / fs + phase), dt = |f| / fs; E(x) = (1 - x)^3 / 6 for x < 1, else 0;
d0 = min(u, 1 - u), d1 = |u - 1/2|; c = -E(d0 / dt) + E(d1 / dt);
y = A((4|u - 1/2| - 1) + 8 dt c), rounded once.

E is the residual of the unit ramp: the integral of the unit step's PolyBLEP residual, derived
in ADR 0314 from the residual of ADR 0310.

Run from the repo root: python vectors/generators/polyblep_triangle.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def blamp(d, dt):
    if dt == 0 or d >= dt:
        return Fr(0)
    return (1 - d / dt) ** 3 / 6


def step_residual(x):
    """The unit step's two-sample residual from ADR 0310: r / 2."""
    if 0 <= x < 1:
        return -(1 - x) ** 2 / 2
    if -1 < x < 0:
        return (1 + x) ** 2 / 2
    return Fr(0)


def big_e(x):
    return (1 - abs(x)) ** 3 / 6 if abs(x) < 1 else Fr(0)


# E is the integral of the step residual. The residual is quadratic on each side of 0, so
# Simpson's rule is exact on every eighth-sample piece; the piece ending at 0 takes the left
# limit 1/2 there.
for k in range(-8, 8):
    lo, hi = Fr(k, 8), Fr(k + 1, 8)
    right = Fr(1, 2) if hi == 0 else step_residual(hi)
    simpson = (hi - lo) / 6 * (step_residual(lo) + 4 * step_residual((lo + hi) / 2) + right)
    assert big_e(hi) - big_e(lo) == simpson, k
assert all(blamp(Fr(k, 9), Fr(1)) == big_e(Fr(k, 9)) for k in range(12))


def add(cid, fs, size, f, why, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    dt = abs(Fr(f)) / Fr(fs)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        c = -blamp(min(u, 1 - u), dt) + blamp(abs(u - Fr(1, 2)), dt)
        y.append(float(a * ((4 * abs(u - Fr(1, 2)) - 1) + 8 * dt * c)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"polyblep_triangle.{cid}", "op": "polyblep_triangle", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("eighth", 8000.0, 8, 1000.0, "eight samples a cycle: only the corner samples change, by "
        "8 dt / 6 = 1/6")
assert y == [1 - 1 / 6, 0.5, 0.0, -0.5, -1 + 1 / 6, -0.5, 0.0, 0.5], y
add("offset", 8000.0, 16, 1000.0, "phase 1/16: every sample sits half a sample from a corner",
    phase=0.0625)
add("non_dyadic", 44100.0, 64, 1234.5, "1234.5 Hz at 44.1 kHz", amplitude=0.6, phase=0.3)
add("falling", 48000.0, 48, -2500.0, "a negative frequency: the same residual, E is even")
add("overlap", 8000.0, 12, 3000.0, "f above fs/4: the corners' regions overlap and add",
    phase=0.1)
add("nyquist", 8000.0, 8, 4000.0, "f = fs/2, dt = 1/2", phase=0.125)
add("still", 8000.0, 4, 0.0, "f = 0: no residual, the naive shape", phase=0.75)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"polyblep_triangle.{cid}", "op": "polyblep_triangle", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=4001.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "polyblep_triangle",
    "description": "PolyBLEP triangle (conventions: PolyBLEP triangle; ADR 0314).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "polyblep_triangle.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/polyblep_triangle.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
