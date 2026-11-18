"""Writes vectors/cases/phase_distortion.json, stdlib only.

Phase-distortion oscillator (conventions: Phase-distortion oscillator; ADR 0319): in exact
rationals, u = frac(f n / fs + phase), w = u / (2k) for u < k, else 1/2 + (u - k) / (2 (1 - k));
w rounded once; y = -A cos(2 pi w) with math.cos.

Run from the repo root: python vectors/generators/phase_distortion.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, fs, size, f, knee, why, amplitude=None, phase=None):
    a = 1.0 if amplitude is None else amplitude
    p0 = Fr(0 if phase is None else phase)
    k = Fr(knee)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        w = u / (2 * k) if u < k else Fr(1, 2) + (u - k) / (2 * (1 - k))
        y.append(-a * math.cos(2 * math.pi * float(w)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f, "knee": knee}
    for name, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[name] = v
    cases.append({"id": f"phase_distortion.{cid}", "op": "phase_distortion", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("cosine", 8000.0, 8, 1000.0, 0.5, "knee 1/2: w = u, a pure -cos")
assert all(abs(v + math.cos(2 * math.pi * n / 8)) < 1e-15 for n, v in enumerate(y)), y
y = add("quarter", 8000.0, 8, 1000.0, 0.25, "knee 1/4: the trough-to-peak half takes two "
        "samples, w = 0, 1/4, 1/2, 2/3, 5/6, 1, 7/6, 4/3")
assert abs(y[1]) < 1e-15 and y[2] == 1.0, y
add("bright", 48000.0, 64, 750.0, 0.05, "knee 1/20: nearly a rising edge, then a slow fall",
    amplitude=0.8)
add("dark", 44100.0, 48, 1234.5, 0.9, "knee 9/10: a slow rise, then a quick fall", phase=0.3)
add("falling", 8000.0, 16, -500.0, 0.125, "a negative frequency runs the phase backwards")


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0, "knee": 0.25}
    base.update(args)
    cases.append({"id": f"phase_distortion.{cid}", "op": "phase_distortion", "args": base,
                  "error": "invalid_argument", "source": why})


err("knee_zero", "knee must be above 0", knee=0.0)
err("knee_one", "knee must be below 1", knee=1.0)
err("knee_nan", "knee must be finite", knee="nan")
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "phase_distortion",
    "description": "Phase-distortion oscillator (conventions: Phase-distortion oscillator; "
    "ADR 0319).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "phase_distortion.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/phase_distortion.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
