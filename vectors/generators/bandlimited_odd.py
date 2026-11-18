"""Writes vectors/cases/bandlimited_odd.json, stdlib only.

Band-limited square and triangle (conventions: Band-limited square and triangle; ADR 0309):
u = frac(f n / fs + phase) in exact rationals, K the largest k with k |f| < fs / 2 (exact here);
square (4A / pi) sum_{odd k <= K} sin(2 pi k u) / k, triangle
(8A / pi^2) sum_{odd k <= K} cos(2 pi k u) / k^2, with stdlib math.

Run from the repo root: python vectors/generators/bandlimited_odd.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []
SERIES = {
    "bandlimited_square": (lambda k, u: math.sin(2 * math.pi * k * u) / k, 4 / math.pi),
    "bandlimited_triangle": (lambda k, u: math.cos(2 * math.pi * k * u) / k**2, 8 / math.pi**2),
}


def add(op, cid, fs, size, f, why, amplitude=None, phase=None):
    term, scale = SERIES[op]
    a = 1.0 if amplitude is None else amplitude
    p = Fr(0 if phase is None else phase)
    top = 0
    while Fr(top + 1) * abs(Fr(f)) < Fr(fs) / 2:
        top += 1
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p
        u = float(t - math.floor(t))
        y.append(a * scale * math.fsum(term(k, u) for k in range(1, top + 1, 2)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f}
    for k, v in (("amplitude", amplitude), ("phase", phase)):
        if v is not None:
            args[k] = v
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "expected": y, "tol": TOL,
                  "source": why})
    return y, top


for op in SERIES:
    y, top = add(op, "fundamental", 8000.0, 16, 2000.0, "f = fs/4: K = 1, the fundamental")
    assert top == 1
    y, top = add(op, "even_top", 8000.0, 16, 1000.0, "f = fs/8: K = 3, harmonics 1 and 3")
    assert top == 3
    add(op, "several", 48000.0, 48, 1500.0, "1500 Hz at 48 kHz: K = 15", amplitude=0.5,
        phase=0.125)
    add(op, "falling", 48000.0, 40, -2500.0, "a negative frequency: K = 9")
    add(op, "non_dyadic", 44100.0, 40, 1234.5, "1234.5 Hz at 44.1 kHz: K = 17", phase=0.3)
    cases.append({"id": f"{op}.frequency_zero", "op": op,
                  "args": {"sample_rate": 8000.0, "num_samples": 4, "frequency": 0.0},
                  "error": "invalid_argument", "source": "frequency must not be 0"})
y, _ = add("bandlimited_square", "edge", 8000.0, 4, 4000.0, "f = fs/2: K = 0, silence")
assert y == [0.0] * 4

doc = {
    "schema": 1,
    "suite": "bandlimited_odd",
    "description": "Band-limited square and triangle (conventions: Band-limited square and "
    "triangle; ADR 0309).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bandlimited_odd.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bandlimited_odd.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
