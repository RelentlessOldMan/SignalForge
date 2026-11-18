"""Writes vectors/cases/tilt_eq.json, stdlib only.

Tilt EQ (conventions: Tilt EQ; ADR 0283): the bilinear transform s = (1/t)(1 - z^-1)/(1 + z^-1)
of H(s) = (T s + 1)/(s + T), done in exact rationals at the float t = tan(pi f/fs) and
T = 10^(gain_db/40). The DC and fs/2 gains, 1/T and T, are checked exactly.

Run from the repo root: python vectors/generators/tilt_eq.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def design(f, gdb, fs):
    t = Fr(math.tan(math.pi * f / fs))
    big_t = Fr(10 ** (gdb / 40))
    # Multiply numerator T s + 1 and denominator s + T by t (1 + z^-1).
    b = [big_t + t, t - big_t]
    a = [1 + big_t * t, big_t * t - 1]
    assert sum(b) / sum(a) == 1 / big_t
    assert (b[0] - b[1]) / (a[0] - a[1]) == big_t
    return [[float(b[0] / a[0]), float(b[1] / a[0]), 0.0, 1.0, float(a[1] / a[0]), 0.0]]


def add(cid, f, gdb, fs, why):
    cases.append({"id": f"tilt_eq.{cid}", "op": "tilt_eq",
                  "args": {"frequency": f, "gain_db": gdb, "sample_rate": fs},
                  "expected": design(f, gdb, fs), "tol": TOL, "source": why})


add("bright", 1000.0, 6.0, 48000.0, "+6 dB tilt about 1 kHz at 48 kHz")
add("dark", 0.1, -10.0, 1.0, "-10 dB tilt about 0.1 fs")
add("flat", 0.25, 0.0, 1.0, "0 dB: unity")
add("high_pivot", 0.45, 3.0, 1.0, "pivot near fs/2")


def err(cid, why, **args):
    base = {"frequency": 1.0, "gain_db": 3.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"tilt_eq.{cid}", "op": "tilt_eq", "args": base,
                  "error": "invalid_argument", "source": why})


err("frequency_zero", "frequency must be positive", frequency=0.0)
err("frequency_nyquist", "frequency must be below fs/2", frequency=4.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "tilt_eq",
    "description": "Tilt EQ (conventions: Tilt EQ; ADR 0283).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tilt_eq.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tilt_eq.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
