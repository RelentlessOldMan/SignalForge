"""Writes vectors/cases/spectral_shape.json in exact fractions, stdlib only.

The PSD is a step density, constant over each bin (conventions: Spectra, Spectral skewness and
kurtosis; ADR 0126). The generator integrates the raw moments E f^j piece by piece with
Fractions, then expands them binomially about the centroid. That route differs from the
libraries', which integrate about the centroid directly. Hand-known values (the uniform
distribution's 0 and 9/5) are asserted exactly.

Run from the repo root: python vectors/generators/spectral_shape.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F
from math import comb

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def central(freqs, psd, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    raw = [F(0)] * 5
    for f_l, f_r, p in zip(left, right, psd):
        d = F(p) * delta / (f_r - f_l)
        a, b = max(f_l, lo), min(f_r, hi)
        if b <= a:
            continue
        for j in range(5):
            raw[j] += d * (b ** (j + 1) - a ** (j + 1)) / (j + 1)
    e = [r / raw[0] for r in raw]
    c = e[1]
    return [sum(comb(j, i) * e[i] * (-c) ** (j - i) for i in range(j + 1)) for j in range(5)]


def case(cid, args, why, skew=None, kurt=None):
    m = central(args["frequencies"], args["psd"], args.get("band"), args.get("span"))
    k = m[4] / (m[2] * m[2])
    if skew is not None:
        assert m[3] == skew, (cid, m[3])
    if kurt is not None:
        assert k == kurt, (cid, k)
    cases.append({"id": f"spectral_shape.{cid}", "op": "spectral_shape", "args": args,
                  "expected": {"skewness": float(m[3]) / math.sqrt(float(m[2])) ** 3,
                               "kurtosis": float(k)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_shape.{cid}", "op": "spectral_shape", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [1.0] * 4},
     "flat over [-0.5, 3.5] is uniform: skewness 0, kurtosis 9/5", 0, F(9, 5))
case("single_bin", {"frequencies": F4, "psd": [0.0, 3.0, 0.0, 0.0]},
     "one bin is uniform over its width: skewness 0, kurtosis 9/5", 0, F(9, 5))
case("two_ends", {"frequencies": F4, "psd": [1.0, 0.0, 0.0, 1.0]},
     "bins at 0 and 3 cover offsets 1 to 2 either side of the centroid 1.5: skewness 0; "
     "m2 = (2^3 - 1)/3 = 7/3, m4 = (2^5 - 1)/5 = 31/5, kurtosis (31/5) / (49/9) = 279/245",
     0, F(279, 245))
case("leaning_low", {"frequencies": F4, "psd": [4.0, 2.0, 1.0, 1.0]},
     "power falls with frequency, so the tail is high: skewness positive")
case("leaning_high", {"frequencies": F4, "psd": [1.0, 1.0, 2.0, 4.0]},
     "the mirror of leaning_low: the same kurtosis, the skewness negated")
case("cut_band", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 2.0]},
     "flat, band [0, 2] is uniform: skewness 0, kurtosis 9/5", 0, F(9, 5))
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 3.0], "span": [0.0, 3.0]},
     "span (0, 3) halves bins 0 and 3 at doubled density; uneven ends")
case("offset_axis", {"frequencies": [1000.0, 1001.0, 1002.0], "psd": [1.0, 4.0, 2.0]},
     "an uneven three-bin PSD far from zero")

err("band_reversed", {"frequencies": F4, "psd": [1.0] * 4, "band": [2.0, 1.0]},
    "band low must be below band high")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("one_bin", {"frequencies": [0.0], "psd": [1.0]}, "need at least two bins")

doc = {
    "schema": 1,
    "suite": "spectral_shape",
    "description": "Spectral skewness and kurtosis (conventions: Spectra, Spectral skewness and "
    "kurtosis; ADR 0126).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_shape.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_shape.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
