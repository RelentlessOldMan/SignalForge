"""Writes vectors/cases/octave_band_levels.json, stdlib only.

Octave-band levels (conventions: Octave-band levels; ADR 0168). An independent float
implementation: IEC 61260-1 base-10 band edges, each band-pass designed from the analog poles of
the band Butterworth (conventions: band Butterworth) through the bilinear transform, run as a
direct-form-I cascade from rest in plain Python, then the mean of |y|^2.

Run from the repo root: python vectors/generators/octave_band_levels.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-9}
cases = []


def edges(b, lo, hi):
    shift = 0.5 if b % 2 == 0 else 0.0
    out = []
    for x in range(-200, 200):
        fm = 1000 * 10 ** (3 * (x + shift) / (10 * b))
        if lo <= fm <= hi:
            half = 10 ** (3 / (20 * b))
            out.append((fm / half, fm * half))
    return out


def design(order, low, high, fs):
    lo, hi = math.tan(math.pi * low / fs), math.tan(math.pi * high / fs)
    w2, bw = lo * hi, hi - lo
    poles = []
    if order % 2:
        poles.append((-bw / 2, w2))
    for i in range(order // 2):
        theta = math.pi / 2 + math.pi * (2 * i + 1) / (2 * order)
        c = bw * complex(math.cos(theta), math.sin(theta))
        d = cmath.sqrt(c * c - 4 * w2)
        poles += [(s.real, abs(s) ** 2) for s in ((c + d) / 2, (c - d) / 2)]
    rows = []
    for sigma, m in poles:
        a0 = 1 - 2 * sigma + m
        rows.append(([bw / a0, 0.0, -bw / a0], [2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0]))
    return rows


def run(rows, x):
    for (b0, b1, b2), (a1, a2) in rows:
        x1 = x2 = y1 = y2 = 0
        y = []
        for v in x:
            out = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, v, y1, out
            y.append(out)
        x = y
    return x


def levels(x, fs, b, lo, hi, order):
    return [sum(abs(v) ** 2 for v in run(design(order, l, h, fs), x)) / len(x)
            for l, h in edges(b, lo, hi)]


def tone(n, fs, parts):
    return [sum(a * math.cos(2 * math.pi * f * k / fs + p) for a, f, p in parts) for k in range(n)]


def case(cid, samples, fs, b, lo, hi, why, order=None):
    x = [complex(r, i) for r, i in zip(samples["re"], samples["im"])] if isinstance(samples, dict) else samples
    args = {"samples": samples, "sample_rate": fs, "fraction": b, "min_frequency": lo, "max_frequency": hi}
    if order is not None:
        args["order"] = order
    cases.append({"id": f"octave_band_levels.{cid}", "op": "octave_band_levels", "args": args,
                  "expected": levels(x, fs, b, lo, hi, order or 3), "tol": TOL, "source": why})


MIX = tone(160, 8000.0, [(1.0, 1000.0, 0.0), (0.5, 250.0, 0.3), (0.25, 2500.0, 1.1)])
case("thirds_8k", MIX, 8000.0, 3, 200.0, 2600.0,
     "three tones, 160 samples, thirds 200 Hz to 2.6 kHz, order 3: an independent float design and cascade")
case("octaves_8k", MIX, 8000.0, 1, 60.0, 2100.0,
     "the same tones, octaves 63 Hz to 2 kHz: an independent float design and cascade")
case("order_two", MIX, 8000.0, 1, 900.0, 1100.0, "the 1 kHz octave alone, order 2", order=2)
case("complex", {"re": [math.cos(2 * math.pi * 500 * k / 4000) for k in range(64)],
                 "im": [math.sin(2 * math.pi * 500 * k / 4000) for k in range(64)]},
     4000.0, 1, 400.0, 1100.0, "a complex 500 Hz exponential at 4 kHz, octaves 500 and 1000 Hz")
cases.append({"id": "octave_band_levels.no_bands", "op": "octave_band_levels",
              "args": {"samples": [1.0, 0.0], "sample_rate": 8000.0, "fraction": 1,
                       "min_frequency": 1100.0, "max_frequency": 1900.0},
              "expected": [], "tol": TOL, "source": "no octave center lies in 1100 to 1900 Hz"})


def err(cid, change, why):
    args = {"samples": [1.0, 0.0, 0.5], "sample_rate": 8000.0, "fraction": 3,
            "min_frequency": 500.0, "max_frequency": 2000.0}
    args.update(change)
    cases.append({"id": f"octave_band_levels.{cid}", "op": "octave_band_levels", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"samples": []}, "samples must not be empty")
err("nan_sample", {"samples": [1.0, "nan"]}, "samples must be finite")
err("above_nyquist", {"fraction": 1, "max_frequency": 4000.0},
    "the 3981 Hz octave's upper edge 5623 Hz is above 4000 Hz")
err("zero_order", {"order": 0}, "order must be at least 1")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("zero_fraction", {"fraction": 0}, "fraction must be at least 1")

doc = {
    "schema": 1,
    "suite": "octave_band_levels",
    "description": "Octave-band levels (conventions: Octave-band levels; ADR 0168).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "octave_band_levels.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/octave_band_levels.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
