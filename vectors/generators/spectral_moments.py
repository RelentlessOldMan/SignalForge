"""Writes vectors/cases/spectral_moments.json in exact fractions, stdlib only.

The PSD is a step density, constant over each bin (conventions: Spectra, Spectral centroid and
RMS bandwidth; ADR 0121). The generator integrates it piece by piece with Fractions: power as
the integral of d, centroid as the integral of f d over power, and the variance as
E f^2 - centroid^2. That route differs from the libraries', which integrate about the centroid.

Run from the repo root: python vectors/generators/spectral_moments.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def moments(freqs, psd, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    p0 = p1 = p2 = F(0)
    for f_l, f_r, p in zip(left, right, psd):
        d = F(p) * delta / (f_r - f_l)  # the bin keeps its whole power p * delta
        a, b = max(f_l, lo), min(f_r, hi)
        if b <= a:
            continue
        p0 += d * (b - a)
        p1 += d * (b * b - a * a) / 2
        p2 += d * (b**3 - a**3) / 3
    c = p1 / p0
    return p0, c, p2 / p0 - c * c


def case(cid, args, why, want_var=None):
    p0, c, var = moments(args["frequencies"], args["psd"], args.get("band"), args.get("span"))
    if want_var is not None:
        assert var == want_var, (cid, var, want_var)
    cases.append({"id": f"spectral_moments.{cid}", "op": "spectral_moments", "args": args,
                  "expected": {"power": float(p0), "centroid": float(c),
                               "rms_bandwidth": math.sqrt(var)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_moments.{cid}", "op": "spectral_moments", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [1.0] * 4},
     "flat over [-0.5, 3.5]: power 4, centroid 1.5, RMS bandwidth 4/sqrt(12)", F(16, 12))
case("single_bin", {"frequencies": F4, "psd": [0.0, 1.0, 0.0, 0.0]},
     "one bin of width 1 at 1 Hz: power 1, centroid 1, RMS bandwidth 1/sqrt(12)", F(1, 12))
case("two_ends", {"frequencies": F4, "psd": [1.0, 0.0, 0.0, 1.0]},
     "bins at 0 and 3: centroid 1.5; each contributes the integral of (f - 1.5)^2 over its bin, "
     "7/3, so the variance is 7/3", F(7, 3))
case("asymmetric", {"frequencies": F4, "psd": [1.0, 2.0, 0.0, 0.0]},
     "power 3; centroid (0 + 2) / 3 = 2/3; variance (19/36 + 14/36) / 3 = 11/36", F(11, 36))
case("cut_band", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 2.0]},
     "flat, band [0, 2]: power 2, centroid 1, RMS bandwidth 2/sqrt(12)", F(4, 12))
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     "span (0, 3) halves bins 0 and 3, which keep power 2 at density 4; power 6, centroid 1.5, "
     "variance (2 x 9.5/3 + 2 x 1/3) / 6 = 7/6", F(7, 6))
case("offset_axis", {"frequencies": [1000.0, 1001.0, 1002.0], "psd": [1.0, 4.0, 1.0]},
     "symmetric about 1001 Hz: power 6, centroid 1001, variance (4/12 + 2 x (1/12 + 1)) / 6 "
     "= 5/12", F(5, 12))

err("band_reversed", {"frequencies": F4, "psd": [1.0] * 4, "band": [2.0, 1.0]},
    "band low must be below band high")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [-1.0, 3.0]},
    "band [-1, 3] leaves the spectrum [-0.5, 3.5]")
err("band_nan", {"frequencies": F4, "psd": [1.0] * 4, "band": ["nan", 1.0]},
    "band edges must be finite")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("one_bin", {"frequencies": [0.0], "psd": [1.0]}, "need at least two bins")

doc = {
    "schema": 1,
    "suite": "spectral_moments",
    "description": "Spectral centroid and RMS bandwidth (conventions: Spectra, Spectral centroid "
    "and RMS bandwidth; ADR 0121).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_moments.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_moments.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
