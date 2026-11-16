"""Writes vectors/cases/instantaneous_frequency.json, stdlib only.

Instantaneous frequency (conventions: Instantaneous frequency; ADR 0187): f[n] = fs/(2 pi)
arg(z[n+1] conj z[n]) with z the analytic signal of ADR 0185. Expected values come from closed
forms of z at bin frequencies: cos -> e^{j theta} (constant k fs/N), DC + cos -> c + e^{j theta},
two cosines -> e^{j theta1} + a e^{j theta2}; each step angle is kept away from +-pi.

Run from the repo root: python vectors/generators/instantaneous_frequency.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-9, "rel": 1e-12}
cases = []


def add(cid, x, z, fs, why):
    f = []
    for n in range(len(z) - 1):
        a = cmath.phase(z[n + 1] * z[n].conjugate())
        assert abs(a) < 3.0, (cid, n, a)
        f.append(fs * a / (2 * math.pi))
    cases.append({"id": f"instantaneous_frequency.{cid}", "op": "instantaneous_frequency",
                  "args": {"samples": x, "sample_rate": fs},
                  "expected": f, "tol": TOL, "source": why})


def theta(n_, k, phase):
    return [2 * math.pi * k * i / n_ + phase for i in range(n_)]


th = theta(16, 3, 0.4)
add("cos_even", [math.cos(t) for t in th], [cmath.exp(1j * t) for t in th], 1000.0,
    "cos(2 pi 3n/16 + 0.4) at 1 kHz: z = e^{j theta}, every step 3 * 1000/16 = 187.5 Hz")
th = theta(12, 5, 0.0)
add("sin_even", [math.sin(t) for t in th], [-1j * cmath.exp(1j * t) for t in th], 48000.0,
    "sin(2 pi 5n/12) at 48 kHz: z = -j e^{j theta}, every step 5 * 48000/12 = 20 kHz")
th = theta(7, 2, -1.1)
add("cos_odd", [math.cos(t) for t in th], [cmath.exp(1j * t) for t in th], 7.0,
    "N = 7, bin 2, fs = 7: every step 2 Hz")
th = theta(8, 1, 0.0)
add("dc_plus_tone", [0.5 + math.cos(t) for t in th], [0.5 + cmath.exp(1j * t) for t in th],
    8.0, "0.5 + cos(2 pi n/8): z = 0.5 + e^{j theta}; the angle of each step of that closed form")
t1, t2 = theta(32, 2, 0.0), theta(32, 9, 0.3)
add("two_tones", [math.cos(a) + 0.6 * math.cos(b) for a, b in zip(t1, t2)],
    [cmath.exp(1j * a) + 0.6 * cmath.exp(1j * b) for a, b in zip(t1, t2)], 32.0,
    "cos(2 pi 2n/32) + 0.6 cos(2 pi 9n/32 + 0.3): z = e^{j theta1} + 0.6 e^{j theta2}; the "
    "angle of each step, which swings between and beyond 2 and 9 Hz")


def err(cid, x, fs, why):
    cases.append({"id": f"instantaneous_frequency.{cid}", "op": "instantaneous_frequency",
                  "args": {"samples": x, "sample_rate": fs}, "error": "invalid_argument",
                  "source": why})


err("one_sample", [1.0], 10.0, "N = 1: no step")
err("empty", [], 10.0, "empty")
err("zero_rate", [1.0, 0.0, -1.0, 0.0], 0.0, "sample_rate must be positive")
err("inf_rate", [1.0, 0.0, -1.0, 0.0], "inf", "sample_rate must be finite")
err("nan", [1.0, "nan", 0.0], 10.0, "not finite")

doc = {
    "schema": 1,
    "suite": "instantaneous_frequency",
    "description": "Instantaneous frequency (conventions: Instantaneous frequency; ADR 0187).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "instantaneous_frequency.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/instantaneous_frequency.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
