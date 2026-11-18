"""Writes vectors/cases/pwm.json, stdlib only.

Pulse-width modulation (conventions: Pulse-width modulation; ADR 0312), from the rule in exact
rationals: u = frac(f n / fs + phase); y[n] = A for u < duty[n], else -A. Each case keeps u[n]
at least 1e-9 from duty[n] unless both are exact binary fractions, so rounding cannot flip a
sample.

Run from the repo root: python vectors/generators/pwm.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def dyadic(x):
    return x.denominator & (x.denominator - 1) == 0


def add(cid, duty, fs, f, why, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    y = []
    for n, d in enumerate(duty):
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        d = Fr(d)
        assert abs(u - d) > Fr(1, 10**9) or (u == d and dyadic(u)), (cid, n)
        y.append(float(a if u < d else -a))
    args = {"duty": duty, "sample_rate": fs, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"pwm.{cid}", "op": "pwm", "args": args, "expected": y, "tol": TOL,
                  "source": why})
    return y


y = add("constant", [0.5] * 8, 8000.0, 1000.0, "a constant duty: the naive square, the tie at "
        "u = 1/2 going to -A")
assert y == [1.0] * 4 + [-1.0] * 4
y = add("sweep", [k / 16 for k in range(16)], 8000.0, 500.0, "duty rising 1/16 a sample against "
        "u rising 1/16 a sample: u = duty, so every sample is -A")
assert y == [-1.0] * 16
y = add("lead", [(k + 1) / 16 for k in range(16)], 8000.0, 500.0, "duty one step ahead of u: "
        "every sample is A", amplitude=0.5)
assert y == [0.5] * 16
add("sine_duty", [0.5 + 0.4 * math.sin(2 * math.pi * k / 37) for k in range(40)], 44100.0,
    1234.5, "a duty that follows a slow sine, 1234.5 Hz at 44.1 kHz", amplitude=0.8,
    phase=0.3)
add("falling", [0.3, 0.7, 0.2, 0.9, 0.05, 0.6, 0.45, 0.8, 0.15, 0.55], 48000.0, -7000.0,
    "a negative frequency: u falls")
add("edges", [0.0, 1.0, 0.0, 1.0, 0.0, 1.0], 8000.0, 1000.0, "duty 0 is always -A, duty 1 always "
    "A", phase=0.0625)
add("empty", [], 8000.0, 1000.0, "an empty duty gives an empty output")


def err(cid, why, **args):
    base = {"duty": [0.5, 0.5], "sample_rate": 8000.0, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"pwm.{cid}", "op": "pwm", "args": base, "error": "invalid_argument",
                  "source": why})


err("duty_above_one", "duty must be in [0, 1]", duty=[0.5, 1.25])
err("duty_negative", "duty must be in [0, 1]", duty=[-0.5, 0.5])
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "pwm",
    "description": "Pulse-width modulation (conventions: Pulse-width modulation; ADR 0312).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pwm.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pwm.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
