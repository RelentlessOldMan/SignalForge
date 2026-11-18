"""Writes vectors/cases/auto_wah.json, stdlib only.

Auto-wah (conventions: Auto-wah; ADR 0280): the ADR 0279 state-variable band-pass, scaled to
unity peak, with g recomputed per sample from the ADR 0238 envelope. The envelope is computed in
exact rationals and rounded; the cutoff, math.tan and the TPT recursion are stdlib floats. The
fixed case is checked against k times the band-pass of the direct-form biquad.

Run from the repo root: python vectors/generators/auto_wah.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def envelope(mags, a, r):
    out, prev = [], Fr(0)
    for m in mags:
        m = Fr(m)
        c = Fr(a) if m > prev else Fr(r)
        prev = m + c * (prev - m)
        out.append(float(prev))
    return out


def band(v, gs, k):
    ic1 = ic2 = 0.0
    out = []
    for x, g in zip(v, gs):
        a1 = 1 / (1 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        out.append(v1)
    return out


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


def run(re, im, low, high, q, a, r, fs, mix):
    mags = [abs(complex(x, y)) for x, y in zip(re, im)] if im is not None else [abs(x) for x in re]
    e = envelope(mags, a, r)
    k = 1 / q
    gs = [math.tan(math.pi * (low + (high - low) * min(v, 1.0)) / fs) for v in e]
    yr = [x * (1 - mix) + k * w * mix for x, w in zip(re, band(re, gs, k))]
    yi = None if im is None else [x * (1 - mix) + k * w * mix for x, w in zip(im, band(im, gs, k))]
    return yr, yi


def add(cid, x, low, high, q, a, r, fs, mix, why):
    y, _ = run(x, None, low, high, q, a, r, fs, mix)
    cases.append({"id": f"auto_wah.{cid}", "op": "auto_wah",
                  "args": {"samples": x, "low": low, "high": high, "q": q, "attack": a,
                           "release": r, "sample_rate": fs, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})
    return y


M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
y = add("fixed", M, 0.1, 0.1, 2.0, 0.5, 0.5, 1.0, 1.0,
        "low = high = 0.1 fs, q 2, wet: k times the fixed band-pass")
ref = biquad(M, 0.1, 2.0, 1.0)["bandpass"]
assert all(abs(got - float(Fr(1, 2) * b)) <= 1e-13 for got, b in zip(y, ref))
add("swept", M, 0.02, 0.3, 4.0, 0.25, 0.75, 1.0, 0.7,
    "0.02 to 0.3 fs, q 4, attack 1/4, release 3/4, mix 0.7")
add("loud", [2.0, -3.0, 2.5, -2.0, 4.0, -1.5, 3.0, -2.5], 100.0, 2000.0, 1.5, 0.0, 0.9, 8000.0,
    0.5, "envelope above 1 from the start: the cutoff sits at high, 2 kHz at 8 kHz")
add("dry", [0.5, -1.0, 2.0], 0.1, 0.2, 1.0, 0.5, 0.5, 1.0, 0.0, "mix 0: the dry signal")

cre, cim = [1.0, 0.0, -0.5, 0.25, 0.75, -0.25], [0.0, 1.0, 0.5, -1.0, 0.0, 0.5]
yr, yi = run(cre, cim, 0.05, 0.25, 3.0, 0.5, 0.5, 1.0, 0.5)
cases.append({"id": "auto_wah.complex", "op": "auto_wah",
              "args": {"samples": {"re": cre, "im": cim}, "low": 0.05, "high": 0.25, "q": 3.0,
                       "attack": 0.5, "release": 0.5, "sample_rate": 1.0, "mix": 0.5},
              "expected": {"re": yr, "im": yi}, "tol": TOL,
              "source": "complex: envelope of |x|, filter part by part"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "low": 1.0, "high": 3.0, "q": 2.0, "attack": 0.5,
            "release": 0.5, "sample_rate": 8.0, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"auto_wah.{cid}", "op": "auto_wah", "args": base,
                  "error": "invalid_argument", "source": why})


err("low_zero", "low must be positive", low=0.0)
err("high_nyquist", "high must be below fs/2", high=4.0)
err("q_zero", "q must be positive", q=0.0)
err("release_one", "release must be below 1", release=1.0)
err("mix_high", "mix must be at most 1", mix=2.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "auto_wah",
    "description": "Auto-wah (conventions: Auto-wah; ADR 0280).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "auto_wah.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/auto_wah.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
