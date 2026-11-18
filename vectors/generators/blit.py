"""Writes vectors/cases/blit.json, stdlib only.

Bandlimited impulse train (conventions: Bandlimited impulse train; ADR 0320), from the
definition, not the closed form: H the number of m >= 1 with m |f| < fs / 2, in exact
rationals; u = frac(f n / fs + phase) exactly, rounded once;
y = A (1 + 2 sum_{m=1}^{H} cos(2 pi m u)) / (2H + 1) with math.cos and math.fsum.

Run from the repo root: python vectors/generators/blit.py [--check]
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
    a = 1.0 if amplitude is None else amplitude
    p0 = Fr(0 if phase is None else phase)
    h = 0
    while (h + 1) * abs(Fr(f)) < Fr(fs) / 2:
        h += 1
    # Keep away from fs / (2|f|) within a rounding of an integer that it is not.
    r = Fr(fs) / (2 * abs(Fr(f)))
    assert r.denominator == 1 or abs(r - round(r)) > Fr(1, 10**6)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        u = float(t - math.floor(t))
        s = math.fsum([1.0] + [2 * math.cos(2 * math.pi * m * u) for m in range(1, h + 1)])
        y.append(a * s / (2 * h + 1))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for name, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[name] = v
    cases.append({"id": f"blit.{cid}", "op": "blit", "args": args, "expected": y, "tol": TOL,
                  "source": why})
    return y, h


y, h = add("eighth", 8000.0, 16, 1000.0, "f = fs/8: harmonics 1, 2, 3 (4 is at Nyquist), M = 7")
assert h == 3 and y[0] == 1.0, (h, y)
y, h = add("odd_ratio", 8000.0, 24, 1600.0, "fs/(2f) = 2.5: H = 2, M = 5", amplitude=0.5)
assert h == 2
add("many", 44100.0, 64, 441.0, "441 Hz at 44.1 kHz: H = 49, M = 99")
add("offset", 48000.0, 40, 1234.5, "a non-dyadic frequency and phase 0.3", phase=0.3)
add("falling", 8000.0, 16, -1000.0, "a negative frequency: the same even sum, phase reversed",
    phase=0.125)
y, h = add("nyquist", 8000.0, 4, 4000.0, "f = fs/2: no harmonics below Nyquist, y = A",
           amplitude=2.0)
assert h == 0 and y == [2.0] * 4


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"blit.{cid}", "op": "blit", "args": base, "error": "invalid_argument",
                  "source": why})


err("zero_frequency", "frequency must be non-zero", frequency=0.0)
err("above_nyquist", "|frequency| must be at most sample_rate / 2", frequency=4000.5)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "blit",
    "description": "Bandlimited impulse train (conventions: Bandlimited impulse train; ADR 0320).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "blit.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/blit.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
