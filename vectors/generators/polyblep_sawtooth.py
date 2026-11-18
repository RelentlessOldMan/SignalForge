"""Writes vectors/cases/polyblep_sawtooth.json, stdlib only.

PolyBLEP sawtooth (conventions: PolyBLEP sawtooth; ADR 0310), from the rule in exact rationals:
u = frac(f n / fs + phase), dt = |f| / fs; r = 2t - t^2 - 1 for t = u / dt when u < dt, else
r = t^2 + 2t + 1 for t = (u - 1) / dt when u > 1 - dt, else 0; y = A((2u - 1) - r), rounded once.

Run from the repo root: python vectors/generators/polyblep_sawtooth.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, fs, size, f, why, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    dt = abs(Fr(f)) / Fr(fs)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = t - math.floor(t)
        if u < dt:
            t = u / dt
            r = 2 * t - t * t - 1
        elif u > 1 - dt:
            t = (u - 1) / dt
            r = t * t + 2 * t + 1
        else:
            r = Fr(0)
        y.append(float(a * ((2 * u - 1) - r)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"polyblep_sawtooth.{cid}", "op": "polyblep_sawtooth", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("eighth", 8000.0, 9, 1000.0, "eight samples a cycle: dt = 1/8, so only the samples "
        "next to the jump change")
assert y[:3] == [-1.0 + 1.0, -0.75, -0.5] and y[7] == 0.75 - 0.0
add("offset", 8000.0, 24, 1000.0, "phase 1/16 puts samples inside both residual regions",
    phase=0.0625)
add("non_dyadic", 44100.0, 64, 1234.5, "1234.5 Hz at 44.1 kHz", amplitude=0.6, phase=0.3)
add("falling", 48000.0, 48, -2500.0, "a negative frequency: the same residual in u")
add("nyquist", 8000.0, 8, 4000.0, "f = fs/2, dt = 1/2: the regions meet but do not overlap",
    phase=0.25)
add("still", 8000.0, 4, 0.0, "f = 0: no residual, the naive shape", phase=0.75)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"polyblep_sawtooth.{cid}", "op": "polyblep_sawtooth", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=4001.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "polyblep_sawtooth",
    "description": "PolyBLEP sawtooth (conventions: PolyBLEP sawtooth; ADR 0310).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "polyblep_sawtooth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/polyblep_sawtooth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
