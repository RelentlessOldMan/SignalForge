"""Writes vectors/cases/dpw_sawtooth.json, stdlib only.

DPW sawtooth (conventions: DPW sawtooth; ADR 0317), from the rule in exact rationals:
u[n] = frac(f n / fs + phase) for n >= -1, x = 2u - 1, y[n] = A (x[n]^2 - x[n-1]^2) fs / (4 f);
at f = 0, y = A x; rounded once.

Run from the repo root: python vectors/generators/dpw_sawtooth.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-11, "rel": 1e-11}
cases = []


def add(cid, fs, size, f, why, amplitude=None, phase=None):
    a = Fr(1 if amplitude is None else amplitude)
    p0 = Fr(0 if phase is None else phase)
    assert f == 0 or abs(Fr(f) / Fr(fs)) >= Fr(1, 200)

    def x(n):
        t = Fr(f) * n / Fr(fs) + p0
        return 2 * (t - math.floor(t)) - 1

    if f == 0:
        y = [float(a * x(n)) for n in range(size)]
    else:
        scale = Fr(fs) / (4 * Fr(f))
        y = [float(a * (x(n) ** 2 - x(n - 1) ** 2) * scale) for n in range(size)]
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"dpw_sawtooth.{cid}", "op": "dpw_sawtooth", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("eighth", 8000.0, 9, 1000.0, "eight samples a cycle: x steps by 1/4, so y[n] is the "
        "mean of x[n] and x[n-1]; across the wrap, (1 - 9/16) 2 = 7/8")
assert y == [0.875, -0.875, -0.625, -0.375, -0.125, 0.125, 0.375, 0.625, 0.875], y
add("offset", 8000.0, 24, 1000.0, "phase 1/16 moves the wrap off the samples", phase=0.0625)
add("non_dyadic", 44100.0, 64, 1234.5, "1234.5 Hz at 44.1 kHz", amplitude=0.6, phase=0.3)
add("falling", 48000.0, 48, -2500.0, "a negative frequency: the falling sawtooth")
add("nyquist", 8000.0, 8, 4000.0, "f = fs/2: x alternates, y is 0", phase=0.25)
add("still", 8000.0, 4, 0.0, "f = 0: the naive shape", phase=0.75)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"dpw_sawtooth.{cid}", "op": "dpw_sawtooth", "args": base,
                  "error": "invalid_argument", "source": why})


err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=-4001.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "dpw_sawtooth",
    "description": "DPW sawtooth (conventions: DPW sawtooth; ADR 0317).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dpw_sawtooth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/dpw_sawtooth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
