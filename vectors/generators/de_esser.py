"""Writes vectors/cases/de_esser.json, stdlib only.

De-esser (conventions: De-esser; ADR 0286): the sidechain compressor of ADR 0278 keyed on
(1/q) times the ADR 0279 state-variable band-pass. The SVF is run in stdlib floats and checked
against the direct-form band-pass biquad in exact rationals; the envelope is exact rationals; the
level, gain and factor are stdlib floats, as in vectors/generators/duck.py.

Run from the repo root: python vectors/generators/de_esser.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-11}
cases = []


def envelope(mags, a, r):
    out, prev = [], Fr(0)
    for m in mags:
        m = Fr(m)
        c = Fr(a) if m > prev else Fr(r)
        prev = m + c * (prev - m)
        out.append(prev)
    return out


def gain(lv, t, r, w):
    d = lv - t
    s = 1 / r - 1
    if 2 * d < -w:
        return 0.0
    if 2 * d > w:
        return s * d
    if w == 0:
        return 0.0
    q = d + w / 2
    return s * q * q / (2 * w)


def run(mags, t, r, a, rel, w, mk):
    f = []
    for e in envelope(mags, a, rel):
        g = gain(20 * math.log10(float(e)), t, r, w) if e > 0 else 0.0
        f.append(10.0 ** ((g + mk) / 20))
    return f


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


def add(cid, x, fc, q, t, r, a, rel, fs, why):
    g = math.tan(math.pi * fc / fs)
    k = 1 / q
    key = [k * v for v in band(x, [g] * len(x), k)]
    ref = biquad(x, fc, q, fs)["bandpass"]
    assert all(abs(got - float(Fr(k) * b)) <= 1e-13 for got, b in zip(key, ref))
    f = run([abs(v) for v in key], t, r, a, rel, 0.0, 0.0)
    cases.append({"id": f"de_esser.{cid}", "op": "de_esser",
                  "args": {"samples": x, "cutoff": fc, "q": q, "threshold_db": t, "ratio": r,
                           "attack": a, "release": rel, "sample_rate": fs},
                  "expected": [v * m for v, m in zip(x, f)], "tol": TOL, "source": why})


# A low tone with a burst at fs/4 in the middle: the burst drives the key.
X = [0.5, 0.45, 0.4, 1.0, 0.3, -1.0, 0.2, 1.0, 0.1, -1.0, 0.0, -0.05, -0.1, -0.15]
add("burst", X, 0.25, 2.0, -12.0, 4.0, 0.0, 0.5, 1.0, "key at fs/4, q 2, -12 dB, ratio 4")
add("smoothed", X, 0.25, 1.0, -20.0, 2.0, 0.5, 0.875, 1.0, "attack 1/2, release 7/8, ratio 2")
add("quiet", [0.01, -0.02, 0.015, -0.01, 0.02], 6000.0, 3.0, 0.0, 10.0, 0.0, 0.0, 48000.0,
    "key below threshold everywhere: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "cutoff": 1.0, "q": 1.0, "threshold_db": 0.0, "ratio": 2.0,
            "attack": 0.5, "release": 0.5, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"de_esser.{cid}", "op": "de_esser", "args": base,
                  "error": "invalid_argument", "source": why})


err("cutoff_nyquist", "cutoff must be below fs/2", cutoff=4.0)
err("q_zero", "q must be positive", q=0.0)
err("ratio_low", "ratio must be at least 1", ratio=0.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "de_esser",
    "description": "De-esser (conventions: De-esser; ADR 0286).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "de_esser.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/de_esser.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
