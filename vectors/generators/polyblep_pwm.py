"""Writes vectors/cases/polyblep_pwm.json, stdlib only.

PolyBLEP pulse-width modulation (conventions: PolyBLEP pulse-width modulation; ADR 0313), from
the rule in exact rationals: u = frac(f n / fs + phase), dt = |f| / fs, d = duty[n];
r(x) = 2t - t^2 - 1 for t = x / dt when x < dt, else t^2 + 2t + 1 for t = (x - 1) / dt when
x > 1 - dt, else 0; v = u - d (+1 when u < d); y = s + A r(u) - A r(v), s = A for u < d else
-A; rounded once.

Run from the repo root: python vectors/generators/polyblep_pwm.py [--check]
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


def add(cid, duty, fs, f, why, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    dt = abs(Fr(f)) / Fr(fs)
    y = []
    for n, d in enumerate(duty):
        d = Fr(d)
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        v = u - d + (1 if u < d else 0)
        s = a if u < d else -a
        y.append(float(s + a * blep(u, dt) - a * blep(v, dt)))
    args = {"duty": duty, "sample_rate": fs, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"polyblep_pwm.{cid}", "op": "polyblep_pwm", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("constant", [0.5] * 16, 8000.0, 1000.0, "a constant duty: the PolyBLEP square",
        phase=0.0625)
assert y[:4] == [0.75, 1.0, 1.0, 0.75], y
add("sine_duty", [0.5 + 0.4 * math.sin(2 * math.pi * k / 37) for k in range(40)], 44100.0,
    1234.5, "a duty that follows a slow sine, 1234.5 Hz at 44.1 kHz", amplitude=0.8, phase=0.3)
add("steps", [0.25] * 12 + [0.75] * 12, 8000.0, 1000.0, "the duty steps from 1/4 to 3/4",
    phase=0.03125)
add("falling", [0.3, 0.7, 0.2, 0.9, 0.05, 0.6, 0.45, 0.8, 0.15, 0.55], 48000.0, -7000.0,
    "a negative frequency: the same residuals in u")
y = add("edges", [0.0, 1.0, 0.0, 1.0], 8000.0, 1000.0, "duty 0 and 1: the residuals cancel",
        phase=0.0625)
assert y == [-1.0, 1.0, -1.0, 1.0], y
add("empty", [], 8000.0, 1000.0, "an empty duty gives an empty output")


def err(cid, why, **args):
    base = {"duty": [0.5, 0.5], "sample_rate": 8000.0, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"polyblep_pwm.{cid}", "op": "polyblep_pwm", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=4001.0)
err("duty_above_one", "duty must be in [0, 1]", duty=[0.5, 1.25])

doc = {
    "schema": 1,
    "suite": "polyblep_pwm",
    "description": "PolyBLEP pulse-width modulation (conventions: PolyBLEP pulse-width "
    "modulation; ADR 0313).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "polyblep_pwm.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/polyblep_pwm.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
