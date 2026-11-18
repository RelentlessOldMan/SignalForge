"""Writes vectors/cases/eq_sections.json, stdlib only.

Shelving and peaking EQ sections (conventions: Shelving and peaking EQ; ADR 0282). Expected
values are the bilinear transform s = (1/t)(1 - z^-1)/(1 + z^-1), t = tan(w0/2), of the analogue
prototypes, done in exact rationals at the float t, A and sqrt(A), and normalised to a0 = 1.
That is not the sin/cos closed form the implementations use. The DC and fs/2 gains are checked
exactly.

Run from the repo root: python vectors/generators/eq_sections.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def bilinear(p, t):
    n2, n1, n0 = p
    return [n2 + n1 * t + n0 * t * t, 2 * (n0 * t * t - n2), n2 - n1 * t + n0 * t * t]


def design(op, f, gdb, q, fs):
    t = Fr(math.tan(math.pi * f / fs))
    av = 10 ** (gdb / 40)
    a, sa, q = Fr(av), Fr(math.sqrt(av)), Fr(q)
    if op == "peaking_eq":
        num, den, dc, nyq = [1, a / q, 1], [1, 1 / (a * q), 1], 1, 1
    elif op == "low_shelf":
        num, den = [a, a * sa / q, a * a], [a, sa / q, 1]
        dc, nyq = a * a, 1
    else:
        num, den = [a * a, a * sa / q, a], [1, sa / q, a]
        dc, nyq = 1, a * a
    b, d = bilinear([Fr(v) for v in num], t), bilinear([Fr(v) for v in den], t)
    assert sum(b) / sum(d) == dc
    assert (b[0] - b[1] + b[2]) / (d[0] - d[1] + d[2]) == nyq
    return [[float(v / d[0]) for v in b] + [1.0, float(d[1] / d[0]), float(d[2] / d[0])]]


def add(op, cid, f, gdb, q, fs, why):
    cases.append({"id": f"{op}.{cid}", "op": op,
                  "args": {"frequency": f, "gain_db": gdb, "q": q, "sample_rate": fs},
                  "expected": design(op, f, gdb, q, fs), "tol": TOL, "source": why})


R2 = 0.7071067811865476
add("peaking_eq", "boost", 1000.0, 6.0, 1.0, 48000.0, "+6 dB at 1 kHz, q 1, fs 48 kHz")
add("peaking_eq", "cut", 0.1, -12.0, 4.0, 1.0, "-12 dB at 0.1 fs, q 4")
add("peaking_eq", "flat", 2000.0, 0.0, 2.0, 8000.0, "0 dB: b equals a")
add("low_shelf", "boost", 200.0, 6.0, R2, 48000.0, "+6 dB below 200 Hz, q 1/sqrt(2)")
add("low_shelf", "cut", 0.05, -9.0, 1.0, 1.0, "-9 dB below 0.05 fs, q 1")
add("low_shelf", "steep", 0.2, 3.0, 2.0, 1.0, "+3 dB, q 2: overshoot near the corner")
add("high_shelf", "boost", 8000.0, 4.5, R2, 48000.0, "+4.5 dB above 8 kHz, q 1/sqrt(2)")
add("high_shelf", "cut", 0.4, -6.0, 0.5, 1.0, "-6 dB above 0.4 fs, q 1/2")
add("high_shelf", "flat", 0.25, 0.0, 1.0, 1.0, "0 dB: unity everywhere")


def err(op, cid, why, **args):
    base = {"frequency": 1.0, "gain_db": 3.0, "q": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"{op}.{cid}", "op": op, "args": base,
                  "error": "invalid_argument", "source": why})


for op in ("peaking_eq", "low_shelf", "high_shelf"):
    err(op, "frequency_zero", "frequency must be positive", frequency=0.0)
    err(op, "frequency_nyquist", "frequency must be below fs/2", frequency=4.0)
    err(op, "q_zero", "q must be positive", q=0.0)

doc = {
    "schema": 1,
    "suite": "eq_sections",
    "description": "Shelving and peaking EQ sections (conventions: Shelving and peaking EQ; "
    "ADR 0282).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "eq_sections.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/eq_sections.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
