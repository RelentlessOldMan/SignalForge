"""Writes vectors/cases/frequency_shift.json, stdlib only.

Frequency shifter (conventions: Frequency shifter; ADR 0301). Analytical: a cosine
A cos(w n + p) at an exact bin 0 < k < N/2 has the analytic signal A e^{j(w n + p)}, so the
output is A cos(w n + p + theta[n]) with theta[n] = (2 pi shift)(n / fs). DC and the Nyquist
bin have no imaginary part, so they come out as x[n] cos theta[n].

Run from the repo root: python vectors/generators/frequency_shift.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 0.0}
cases = []


def theta(n, shift, fs):
    return (2 * math.pi * shift) * (n / fs)


def add(cid, size, parts, dc, nyq, shift, fs, why):
    """parts: (amplitude, bin, phase) cosines; dc and nyq: the DC and Nyquist amplitudes."""
    x, y = [], []
    for n in range(size):
        t = theta(n, shift, fs)
        xv = dc + nyq * (-1) ** n
        yv = xv * math.cos(t)
        for a, k, p in parts:
            w = 2 * math.pi * k / size
            xv += a * math.cos(w * n + p)
            yv += a * math.cos(w * n + p + t)
        x.append(xv)
        y.append(yv)
    cases.append({"id": f"frequency_shift.{cid}", "op": "frequency_shift",
                  "args": {"samples": x, "shift": shift, "sample_rate": fs},
                  "expected": y, "tol": TOL, "source": why})


add("up", 32, [(1.0, 3, 0.0)], 0.0, 0.0, 2.0, 32.0,
    "a cosine at bin 3 of 32, fs 32, shifted up 2 Hz: a cosine at 5 Hz")
add("down", 32, [(0.8, 7, 0.4)], 0.0, 0.0, -3.0, 32.0,
    "bin 7, shifted down 3 Hz, phase kept")
add("two_tones", 48, [(1.0, 4, 0.0), (0.5, 8, 1.1)], 0.0, 0.0, 1.5, 48.0,
    "harmonics 4 and 8 shifted 1.5 Hz to 5.5 and 9.5: no longer harmonic")
add("fractional", 40, [(0.7, 6, -0.3)], 0.0, 0.0, 0.37, 10.0,
    "a fractional shift at fs 10")
add("dc_nyquist", 16, [(0.6, 2, 0.2)], 0.25, -0.4, 1.0, 16.0,
    "DC and Nyquist are amplitude-modulated by cos theta; bin 2 shifts")
add("zero", 16, [(1.0, 5, 0.9)], 0.1, 0.0, 0.0, 16.0, "shift 0: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "shift": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"frequency_shift.{cid}", "op": "frequency_shift", "args": base,
                  "error": "invalid_argument", "source": why})


err("sample_rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "frequency_shift",
    "description": "Frequency shifter (conventions: Frequency shifter; ADR 0301).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "frequency_shift.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/frequency_shift.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
