"""Writes vectors/cases/spectral_slope.json in exact fractions, stdlib only.

The fit is the continuous least-squares line through the PSD's step function over a band
(conventions: Spectra, Spectral slope; ADR 0127). The generator solves the uncentered 2x2 normal
equations in S0 = integral of 1, S1 = of f, S2 = of f^2, T0 = of y and T1 = of y f with
Fractions. That route differs from the libraries', which centre the axis on the band. dB cases
use powers of ten, so every 10 log10 is an exact integer. Hand-known values are asserted: a
flat PSD's slope 0, and a line sampled into M bins giving beta (1 - 1/M^2).

Run from the repo root: python vectors/generators/spectral_slope.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def db_of(x):
    k = 0
    while x >= 10:
        x, k = x / 10, k + 1
    assert x == 1, "dB cases must be powers of ten"
    return F(10 * k)


def fit(freqs, psd, band=None, span=None, db=False):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    s0 = s1 = s2 = t0 = t1 = F(0)
    for f_l, f_r, p in zip(left, right, psd):
        a, b = max(f_l, lo), min(f_r, hi)
        if b <= a:
            continue
        d = F(p) * delta / (f_r - f_l)
        y = db_of(d) if db else d
        s0 += b - a
        s1 += (b * b - a * a) / 2
        s2 += (b**3 - a**3) / 3
        t0 += y * (b - a)
        t1 += y * (b * b - a * a) / 2
    slope = (s0 * t1 - s1 * t0) / (s0 * s2 - s1 * s1)
    center = (lo + hi) / 2
    return center, (t0 - slope * s1) / s0 + slope * center, slope


def case(cid, args, why, slope=None, level=None):
    c, lv, sl = fit(args["frequencies"], args["psd"], args.get("band"), args.get("span"),
                    args.get("db", False))
    if slope is not None:
        assert sl == slope, (cid, sl, slope)
    if level is not None:
        assert lv == level, (cid, lv, level)
    cases.append({"id": f"spectral_slope.{cid}", "op": "spectral_slope", "args": args,
                  "expected": {"center": float(c), "level": float(lv), "slope": float(sl)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_slope.{cid}", "op": "spectral_slope", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
F8 = [float(k) for k in range(8)]
case("flat", {"frequencies": F4, "psd": [2.0] * 4}, "flat at 2: level 2, slope 0", 0, F(2))
case("line_four", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0]},
     "a line of slope 1 in 4 bins: the staircase gives 1 - 1/16 = 15/16; level 10/4 at 1.5",
     F(15, 16), F(5, 2))
case("line_eight_down", {"frequencies": F8, "psd": [float(8 - k) for k in range(8)]},
     "a line of slope -1 in 8 bins: -(1 - 1/64) = -63/64; level 36/8 = 9/2 at 3.5",
     F(-63, 64), F(9, 2))
case("uneven", {"frequencies": F4, "psd": [4.0, 0.0, 1.0, 3.0]},
     "an uneven PSD with an empty bin; linear fits allow zero bins")
case("db_decades", {"frequencies": F4, "psd": [1.0, 10.0, 100.0, 1000.0], "db": True},
     "0, 10, 20, 30 dB: a dB line of 10 per Hz, so 10 x 15/16; level 15 dB", F(75, 8), F(15))
case("db_uneven", {"frequencies": F4, "psd": [100.0, 1.0, 10.0, 1.0], "db": True},
     "20, 0, 10, 0 dB, an uneven dB staircase")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "band": [0.25, 2.75]},
     "band [0.25, 2.75] cuts bins 0 and 3 to a quarter")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 3.0], "span": [0.0, 3.0]},
     "span (0, 3) halves bins 0 and 3 at doubled density")
case("offset_axis", {"frequencies": [1000.0, 1001.0, 1002.0], "psd": [1.0, 4.0, 2.0]},
     "an uneven three-bin PSD far from zero; the uncentered equations are exact in Fractions")

err("db_zero_bin", {"frequencies": F4, "psd": [1.0, 0.0, 1.0, 1.0], "db": True},
    "with db, every bin in the band must have a positive PSD")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("band_reversed", {"frequencies": F4, "psd": [1.0] * 4, "band": [2.0, 1.0]},
    "band low must be below band high")

doc = {
    "schema": 1,
    "suite": "spectral_slope",
    "description": "Spectral slope (conventions: Spectra, Spectral slope; ADR 0127).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_slope.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_slope.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
