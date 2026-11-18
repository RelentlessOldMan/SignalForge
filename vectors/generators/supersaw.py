"""Writes vectors/cases/supersaw.json, stdlib only.

Supersaw (conventions: Supersaw; ADR 0316). Voice k of V: c_k = detune (2k / (V - 1) - 1) cents
(0 when V = 1), f_k = f 2^(c_k / 1200) in floating point; then, in exact rationals from that
f_k and the float phase k / V, the PolyBLEP sawtooth of ADR 0310: u = frac(f_k n / fs + k / V),
dt = |f_k| / fs, r = 2t - t^2 - 1 for t = u / dt when u < dt, else t^2 + 2t + 1 for
t = (u - 1) / dt when u > 1 - dt, else 0, voice = (2u - 1) - r; y = A (sum of voices) / V,
rounded once.

Run from the repo root: python vectors/generators/supersaw.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-10, "rel": 1e-10}
cases = []


def saw(fs, n, f, p0):
    dt = abs(f) / fs
    t = f * n / fs + p0
    u = t - math.floor(t)
    if u < dt:
        t = u / dt
        r = 2 * t - t * t - 1
    elif u > 1 - dt:
        t = (u - 1) / dt
        r = t * t + 2 * t + 1
    else:
        r = Fr(0)
    return (2 * u - 1) - r


def add(cid, fs, size, f, detune, why, voices=None, amplitude=None):
    v = 7 if voices is None else voices
    a = Fr(1 if amplitude is None else amplitude)
    freqs = [f * 2 ** ((0.0 if v == 1 else detune * (2 * k / (v - 1) - 1)) / 1200)
             for k in range(v)]
    assert all(abs(fk) <= fs / 2 for fk in freqs)
    y = []
    for n in range(size):
        acc = sum(saw(Fr(fs), n, Fr(fk), Fr(k / v)) for k, fk in enumerate(freqs))
        y.append(float(a * acc / v))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f, "detune": detune}
    for k, x in (("voices", voices), ("amplitude", amplitude)):
        if x is not None:
            args[k] = x
    cases.append({"id": f"supersaw.{cid}", "op": "supersaw", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


add("seven", 44100.0, 64, 220.0, 25.0, "the default seven voices over +-25 cents")
add("three", 48000.0, 48, 1234.5, 12.0, "three voices: -12, 0 and +12 cents", voices=3,
    amplitude=0.5)
y = add("one", 8000.0, 9, 1000.0, 30.0, "one voice: no detune, phase 0, the PolyBLEP sawtooth",
        voices=1)
assert y[:3] == [0.0, -0.75, -0.5], y
add("unison", 8000.0, 16, 1000.0, 0.0, "detune 0: four voices at one pitch, phases 0, 1/4, "
    "1/2, 3/4", voices=4)
add("falling", 44100.0, 40, -3000.0, 50.0, "a negative frequency: every voice falls", voices=5)


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0, "detune": 10.0}
    base.update(args)
    cases.append({"id": f"supersaw.{cid}", "op": "supersaw", "args": base,
                  "error": "invalid_argument", "source": why})


err("voices_zero", "voices must be at least 1", voices=0)
err("detune_negative", "detune must be at least 0", detune=-1.0)
err("top_voice_above_nyquist", "4000 Hz detuned up 10 cents is above fs/2",
    frequency=4000.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "supersaw",
    "description": "Supersaw (conventions: Supersaw; ADR 0316).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "supersaw.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/supersaw.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
