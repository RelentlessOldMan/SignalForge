"""Writes vectors/cases/feedback_fm.json, stdlib only.

Feedback FM operator (conventions: Feedback FM operator; ADR 0322): u = frac(f n / fs + phase)
in exact rationals, rounded once; s[-1] = 0, s[n] = sin((2 pi u[n]) + (feedback s[n-1])) with
math.sin; y = A s.

Run from the repo root: python vectors/generators/feedback_fm.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-11, "rel": 1e-11}
cases = []


def add(cid, fs, size, f, fb, why, amplitude=None, phase=None):
    assert size <= 48
    a = 1.0 if amplitude is None else amplitude
    p0 = Fr(0 if phase is None else phase)
    y = []
    prev = 0.0
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = float(t - math.floor(t))
        prev = math.sin(2 * math.pi * u + fb * prev)
        y.append(a * prev)
    args = {"sample_rate": fs, "num_samples": size, "frequency": f, "feedback": fb}
    for name, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[name] = v
    cases.append({"id": f"feedback_fm.{cid}", "op": "feedback_fm", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


y = add("sine", 8000.0, 8, 1000.0, 0.0, "no feedback: sin(2 pi n/8)")
assert y[0] == 0.0 and y[2] == 1.0, y
add("gentle", 8000.0, 32, 250.0, 0.5, "feedback 1/2: a little brighter than a sine")
add("bright", 48000.0, 48, 1000.0, 1.5, "feedback 1.5: close to a sawtooth", amplitude=0.7)
add("offset", 44100.0, 40, 1234.5, 1.0, "a non-dyadic frequency and phase 0.3", phase=0.3)
add("falling", 8000.0, 24, -500.0, 0.8, "a negative frequency")


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0, "feedback": 0.5}
    base.update(args)
    cases.append({"id": f"feedback_fm.{cid}", "op": "feedback_fm", "args": base,
                  "error": "invalid_argument", "source": why})


err("feedback_high", "feedback must be at most 1.5", feedback=1.6)
err("feedback_negative", "feedback must be at least 0", feedback=-0.1)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "feedback_fm",
    "description": "Feedback FM operator (conventions: Feedback FM operator; ADR 0322).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "feedback_fm.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/feedback_fm.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
