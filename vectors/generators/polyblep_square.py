"""Writes vectors/cases/polyblep_square.json, stdlib only.

PolyBLEP square (conventions: PolyBLEP square; ADR 0311), from the rule in exact rationals:
u = frac(f n / fs + phase), dt = |f| / fs; r(x) = 2t - t^2 - 1 for t = x / dt when x < dt, else
t^2 + 2t + 1 for t = (x - 1) / dt when x > 1 - dt, else 0; v = u - d (+1 when u < d);
y = s + A r(u) - A r(v), s = A for u < d else -A; rounded once.

Run from the repo root: python vectors/generators/polyblep_square.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def blep(x, dt):
    if x < dt:
        t = x / dt
        return 2 * t - t * t - 1
    if x > 1 - dt:
        t = (x - 1) / dt
        return t * t + 2 * t + 1
    return Fr(0)


def add(cid, fs, size, f, why, duty=None, amplitude=None, phase=None):
    d = Fr(0.5 if duty is None else duty)
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    dt = abs(Fr(f)) / Fr(fs)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        v = u - d + (1 if u < d else 0)
        s = a if u < d else -a
        y.append(float(s + a * blep(u, dt) - a * blep(v, dt)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("duty", duty), ("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"polyblep_square.{cid}", "op": "polyblep_square", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("eighth", 8000.0, 8, 1000.0, "eight samples a cycle, half duty: the samples at and "
        "before each edge change")
assert y == [0.0, 1.0, 1.0, 1.0, 0.0, -1.0, -1.0, -1.0], y
y = add("offset", 8000.0, 16, 1000.0, "phase 1/16 puts samples inside every residual region",
        phase=0.0625)
assert y[:4] == [0.75, 1.0, 1.0, 0.75], y
add("duty_quarter", 44100.0, 64, 1234.5, "1234.5 Hz at 44.1 kHz, duty 0.3", duty=0.3,
    amplitude=0.6, phase=0.3)
add("narrow", 8000.0, 24, 1000.0, "duty 1/16: the two edges' regions overlap and add",
    duty=0.0625, phase=0.03125)
add("falling", 48000.0, 48, -2500.0, "a negative frequency: the same residuals in u", duty=0.4)
add("nyquist", 8000.0, 8, 4000.0, "f = fs/2: dt = 1/2", phase=0.25)
y = add("duty_zero", 8000.0, 8, 1000.0, "duty 0: the residuals cancel, the naive -A", duty=0.0,
        phase=0.0625)
assert y == [-1.0] * 8, y
y = add("duty_one", 8000.0, 8, 1000.0, "duty 1: the residuals cancel, the naive A", duty=1.0,
        amplitude=2.0)
assert y == [2.0] * 8, y
add("still", 8000.0, 4, 0.0, "f = 0: no residual, the naive shape", duty=0.25, phase=0.75)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"polyblep_square.{cid}", "op": "polyblep_square", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=-4001.0)
err("duty_above_one", "duty must be in [0, 1]", duty=1.5)
err("duty_negative", "duty must be in [0, 1]", duty=-0.25)

doc = {
    "schema": 1,
    "suite": "polyblep_square",
    "description": "PolyBLEP square (conventions: PolyBLEP square; ADR 0311).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "polyblep_square.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/polyblep_square.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
