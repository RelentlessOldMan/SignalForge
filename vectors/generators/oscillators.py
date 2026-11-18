"""Writes vectors/cases/oscillators.json, stdlib only.

Sawtooth, square and triangle oscillators (conventions: Oscillators; ADR 0305), from the phase
in exact rationals: u = frac(f n / fs + phase); sawtooth A(2u - 1), square A for u < duty and -A
after, triangle A(4|u - 1/2| - 1). Each value is rounded once.

Run from the repo root: python vectors/generators/oscillators.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []
SHAPES = {
    "sawtooth": lambda u, a, d: a * (2 * u - 1),
    "square": lambda u, a, d: a if u < d else -a,
    "triangle": lambda u, a, d: a * (4 * abs(u - Fr(1, 2)) - 1),
}


def add(op, cid, fs, size, f, why, duty=None, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    d = Fr(0.5 if duty is None else duty)
    p = Fr(0 if phase is None else phase)
    y = []
    for n in range(size):
        t = Fr(f) * Fr(n) / Fr(fs) + p
        u = t - math.floor(t)
        y.append(float(SHAPES[op](u, a, d)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("duty", duty), ("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "expected": y, "tol": TOL,
                  "source": why})
    return y


# 1000 Hz at 8000 Hz with a sixteenth of a cycle of phase keeps u off the jumps, exactly.
y = add("sawtooth", "eighth", 8000.0, 12, 1000.0, "eight samples a cycle, phase 1/16",
        phase=0.0625)
assert y[:3] == [-0.875, -0.625, -0.375]
add("sawtooth", "falling", 8000.0, 12, -1000.0, "a negative frequency falls", phase=0.0625,
    amplitude=0.5)
add("sawtooth", "non_dyadic", 48000.0, 40, 440.0, "440 Hz at 48 kHz", phase=0.3)
y = add("square", "half", 8000.0, 12, 1000.0, "duty 1/2", phase=0.0625)
assert y[:8] == [1.0] * 4 + [-1.0] * 4
add("square", "quarter", 8000.0, 12, 1000.0, "duty 1/4, amplitude 2", duty=0.25, amplitude=2.0,
    phase=0.0625)
add("square", "duty_zero", 8000.0, 4, 1000.0, "duty 0: low throughout", duty=0.0)
add("square", "duty_one", 8000.0, 4, 1000.0, "duty 1: high throughout", duty=1.0)
add("square", "non_dyadic", 48000.0, 40, 440.0, "440 Hz at 48 kHz, duty 0.3", duty=0.3,
    phase=0.1)
y = add("triangle", "eighth", 8000.0, 12, 1000.0, "eight samples a cycle, from the peak")
assert y[:8] == [1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5]
add("triangle", "non_dyadic", 48000.0, 40, 440.0, "440 Hz at 48 kHz", amplitude=0.7,
    phase=0.2)


def err(op, cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"{op}.{cid}", "op": op, "args": base, "error": "invalid_argument",
                  "source": why})


err("square", "duty_high", "duty must be at most 1", duty=1.5)
err("sawtooth", "rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("triangle", "count_negative", "num_samples must be at least 0", num_samples=-1)

doc = {
    "schema": 1,
    "suite": "oscillators",
    "description": "Sawtooth, square and triangle oscillators (conventions: Oscillators; "
    "ADR 0305).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "oscillators.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/oscillators.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
