"""Writes vectors/cases/bandlimited_sawtooth.json, stdlib only.

Band-limited sawtooth (conventions: Band-limited sawtooth; ADR 0307): u = frac(f n / fs + phase)
in exact rationals, K the largest k with k |f| < fs / 2 (exact here), and
y = -(2A / pi) sum_{k=1..K} sin(2 pi k u) / k with stdlib math.sin.

Run from the repo root: python vectors/generators/bandlimited_sawtooth.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def add(cid, fs, size, f, why, amplitude=None, phase=None):
    a = 1.0 if amplitude is None else amplitude
    p = Fr(0 if phase is None else phase)
    top = 0
    while Fr(top + 1) * abs(Fr(f)) < Fr(fs) / 2:
        top += 1
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p
        u = float(t - math.floor(t))
        s = math.fsum(math.sin(2 * math.pi * k * u) / k for k in range(1, top + 1))
        y.append(-2 * a / math.pi * s)
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"bandlimited_sawtooth.{cid}", "op": "bandlimited_sawtooth",
                  "args": args, "expected": y, "tol": TOL, "source": why})
    return y, top


y, top = add("fundamental", 8000.0, 16, 2000.0, "f = fs/4: only the fundamental, K = 1")
assert top == 1 and all(abs(v + 2 / math.pi * math.sin(math.pi * n / 2)) < 1e-15
                        for n, v in enumerate(y))
y, top = add("edge", 8000.0, 8, 4000.0, "f = fs/2: k = 1 is on the edge and excluded, K = 0")
assert top == 0 and y == [0.0] * 8
add("several", 48000.0, 48, 1500.0, "1500 Hz at 48 kHz: K = 15", amplitude=0.5, phase=0.125)
add("falling", 48000.0, 40, -2500.0, "a negative frequency runs the phase backwards: K = 9")
add("non_dyadic", 44100.0, 40, 1234.5, "1234.5 Hz at 44.1 kHz: K = 17", phase=0.3)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"bandlimited_sawtooth.{cid}", "op": "bandlimited_sawtooth",
                  "args": base, "error": "invalid_argument", "source": why})


err("frequency_zero", "frequency must not be 0", frequency=0.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "bandlimited_sawtooth",
    "description": "Band-limited sawtooth (conventions: Band-limited sawtooth; ADR 0307).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bandlimited_sawtooth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bandlimited_sawtooth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
