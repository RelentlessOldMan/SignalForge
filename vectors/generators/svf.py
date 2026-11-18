"""Writes vectors/cases/svf.json, stdlib only.

State-variable filter (conventions: State-variable filter; ADR 0279). The expected values are
the direct-form biquad of the bilinear transform of 1/(s^2 + k s + 1) and its band, high and
notch numerators, prewarped to the cutoff, run in exact rationals at the float g that math.tan
returns. Not the TPT recursion the implementations run.

Run from the repo root: python vectors/generators/svf.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def biquad(x, fc, q, fs):
    g = Fr(math.tan(math.pi * fc / fs))
    k = 1 / Fr(q)
    den = 1 + k * g + g * g
    a1, a2 = (2 * g * g - 2) / den, (1 - k * g + g * g) / den
    nums = {
        "lowpass": [g * g, 2 * g * g, g * g],
        "bandpass": [g, Fr(0), -g],
        "highpass": [Fr(1), Fr(-2), Fr(1)],
        "notch": [1 + g * g, 2 * g * g - 2, 1 + g * g],
    }
    out = {}
    for name, b in nums.items():
        b = [c / den for c in b]
        y = []
        for n in range(len(x)):
            acc = Fr(0)
            for i in range(3):
                if n - i >= 0:
                    acc += b[i] * Fr(x[n - i])
            if n >= 1:
                acc -= a1 * y[n - 1]
            if n >= 2:
                acc -= a2 * y[n - 2]
            y.append(acc)
        out[name] = y
    for n in range(len(x)):
        lo, bp, hp, no = (out[m][n] for m in ("lowpass", "bandpass", "highpass", "notch"))
        assert lo + k * bp + hp == Fr(x[n])
        assert no == lo + hp
    return out


def add(cid, x, fc, q, fs, output, why):
    args = {"samples": x, "cutoff": fc, "q": q, "sample_rate": fs}
    if output is not None:
        args["output"] = output
    y = biquad(x, fc, q, fs)[output or "lowpass"]
    cases.append({"id": f"svf.{cid}", "op": "svf", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})


X = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
for out in ("lowpass", "bandpass", "highpass", "notch"):
    add(f"impulse_{out}", X, 1000.0, 0.7071067811865476, 8000.0, out,
        f"impulse response, cutoff fs/8, q 1/sqrt(2), {out}")
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3]
add("default", M, 3000.0, 2.0, 48000.0, None, "no output named: low-pass, cutoff 3 kHz, q 2")
add("resonant_band", M, 0.15, 8.0, 1.0, "bandpass", "cutoff 0.15 fs, q 8, band-pass")
add("near_nyquist_high", M, 0.45, 0.5, 1.0, "highpass", "cutoff 0.45 fs, q 1/2, high-pass")

cre, cim = [1.0, 0.0, -2.0, 0.5, 0.25, 0.0], [0.0, 1.0, 0.5, -1.0, 2.0, 0.0]
yr = biquad(cre, 0.2, 1.5, 1.0)["notch"]
yi = biquad(cim, 0.2, 1.5, 1.0)["notch"]
cases.append({"id": "svf.complex", "op": "svf",
              "args": {"samples": {"re": cre, "im": cim}, "cutoff": 0.2, "q": 1.5,
                       "sample_rate": 1.0, "output": "notch"},
              "expected": {"re": [float(v) for v in yr], "im": [float(v) for v in yi]},
              "tol": TOL, "source": "complex, part by part, notch at 0.2 fs, q 1.5"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "cutoff": 1.0, "q": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"svf.{cid}", "op": "svf", "args": base,
                  "error": "invalid_argument", "source": why})


err("cutoff_zero", "cutoff must be positive", cutoff=0.0)
err("cutoff_nyquist", "cutoff must be below fs/2", cutoff=4.0)
err("q_zero", "q must be positive", q=0.0)
err("output_unknown", "output must name one of the four", output="allpass")
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "svf",
    "description": "State-variable filter (conventions: State-variable filter; ADR 0279).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "svf.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/svf.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
