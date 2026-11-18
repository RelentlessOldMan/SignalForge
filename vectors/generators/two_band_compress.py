"""Writes vectors/cases/two_band_compress.json, stdlib only.

Two-band compressor (conventions: Two-band compressor; ADR 0287). The Linkwitz-Riley bands are
the stdlib Butterworth biquads of vectors/generators/crossover_split.py, run as difference
equations in exact rationals; each band is compressed as in vectors/generators/compress.py
(envelope in exact rationals; level, gain and factor in stdlib floats), and the two are summed.

Run from the repo root: python vectors/generators/two_band_compress.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-11}
cases = []


def butterworth(order, cutoff, fs, high):
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:
        if high:
            rows.append([1 / (k + 1), -1 / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
        else:
            rows.append([k / (k + 1), k / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        iq = 2 * math.sin(math.pi * (2 * i + 1) / (2 * order))
        d = k * k + k * iq + 1
        a = [1.0, 2 * (k * k - 1) / d, (k * k - k * iq + 1) / d]
        b = [1 / d, -2 / d, 1 / d] if high else [k * k / d, 2 * k * k / d, k * k / d]
        rows.append(b + a)
    return rows


def filt(rows, x):
    y = [Fr(v) for v in x]
    for b0, b1, b2, a0, a1, a2 in rows:
        b0, b1, b2, a1, a2 = (Fr(v) for v in (b0, b1, b2, a1, a2))
        assert a0 == 1
        out = []
        for n in range(len(y)):
            acc = b0 * y[n]
            if n >= 1:
                acc += b1 * y[n - 1] - a1 * out[n - 1]
            if n >= 2:
                acc += b2 * y[n - 2] - a2 * out[n - 2]
            out.append(acc)
        y = out
    return [float(v) for v in y]


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


def bands(x, order, fc, fs):
    n = order // 2
    lo, hi = butterworth(n, fc, fs, False), butterworth(n, fc, fs, True)
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    return filt(lo + lo, x), filt(high, x)


def add(cid, x, order, fc, fs, lt, lr, ht, hr, a, rel, why):
    lo, hi = bands(x, order, fc, fs)
    fl = run([abs(v) for v in lo], lt, lr, a, rel, 0.0, 0.0)
    fh = run([abs(v) for v in hi], ht, hr, a, rel, 0.0, 0.0)
    y = [u * p + v * q for u, p, v, q in zip(lo, fl, hi, fh)]
    if lr == 1 and hr == 1:
        assert y == [u + v for u, v in zip(lo, hi)]
    cases.append({"id": f"two_band_compress.{cid}", "op": "two_band_compress",
                  "args": {"samples": x, "order": order, "cutoff": fc, "sample_rate": fs,
                           "low_threshold_db": lt, "low_ratio": lr, "high_threshold_db": ht,
                           "high_ratio": hr, "attack": a, "release": rel},
                  "expected": y, "tol": TOL, "source": why})


M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
B = [2.0, 1.8, 1.5, 1.2, 0.9, 0.6, 0.3, 0.0, -0.3, -0.6, -0.9, -1.2]
add("ratio_one", M, 4, 0.125, 1.0, -20.0, 1.0, -20.0, 1.0, 0.5, 0.5,
    "both ratios 1: the sum of the LR4 bands, the all-pass of the input")
add("low_only", B, 4, 0.1, 1.0, -12.0, 4.0, 0.0, 1.0, 0.0, 0.5,
    "LR4 at 0.1 fs: low band at -12 dB, ratio 4; high band untouched")
add("both", M, 2, 1000.0, 8000.0, -18.0, 3.0, -6.0, 8.0, 0.25, 0.75,
    "LR2 at 1 kHz, fs 8 kHz: each band compressed with its own settings")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "order": 4, "cutoff": 1.0, "sample_rate": 8.0,
            "low_threshold_db": 0.0, "low_ratio": 2.0, "high_threshold_db": 0.0,
            "high_ratio": 2.0, "attack": 0.5, "release": 0.5}
    base.update(args)
    cases.append({"id": f"two_band_compress.{cid}", "op": "two_band_compress", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_odd", "order must be even", order=5)
err("low_ratio_low", "ratio must be at least 1", low_ratio=0.5)
err("high_ratio_low", "ratio must be at least 1", high_ratio=0.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "two_band_compress",
    "description": "Two-band compressor (conventions: Two-band compressor; ADR 0287).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "two_band_compress.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/two_band_compress.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
