"""Writes vectors/cases/harmonic_centroid.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Spectra, Harmonic
centroid; ADR 0145). The heights are perfect squares, so the amplitudes are exact. The centroid
is an exact fraction, and the spread is the square root of one. The generator checks both hand
values against the definition.

Run from the repo root: python vectors/generators/harmonic_centroid.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def definition(tones, heights, orders):
    a, t = [], []
    for f, h, m in zip(tones, heights, orders, strict=True):
        if m >= 1:
            r = math.isqrt(h)
            assert r * r == h, h
            a.append(F(r))
            t.append(F(f))
    c = sum(x * y for x, y in zip(a, t, strict=True)) / sum(a)
    var = sum(x * (y - c) ** 2 for x, y in zip(a, t, strict=True)) / sum(a)
    return c, var


def case(cid, tones, heights, orders, centroid, variance, why):
    assert definition(tones, heights, orders) == (centroid, variance), (
        cid, definition(tones, heights, orders))
    num, den = variance.numerator, variance.denominator
    spread = math.sqrt(num) / math.sqrt(den)
    cases.append({"id": f"harmonic_centroid.{cid}", "op": "harmonic_centroid",
                  "args": {"frequencies": [float(f) for f in tones],
                           "heights": [float(h) for h in heights], "orders": orders},
                  "expected": {"centroid": float(centroid), "spread": spread},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"frequencies": [100.0, 200.0], "heights": [1.0, 1.0], "orders": [1, 2]}
    full.update(args)
    cases.append({"id": f"harmonic_centroid.{cid}", "op": "harmonic_centroid", "args": full,
                  "error": "invalid_argument", "source": why})


case("falling", [100, 200, 300], [9, 4, 1], [1, 2, 3], F(500, 3), F(50000, 9),
     "amplitudes 3, 2, 1: centroid (300 + 400 + 300)/6 = 500/3; squared deviations 40000/9, "
     "10000/9, 160000/9 weighted 3, 2, 1 sum to 300000/9, over 6 is 50000/9")
case("equal", [100, 200, 300, 400], [4, 4, 4, 4], [1, 2, 3, 4], F(250), F(12500),
     "equal weights: mean 250, variance (150² + 50² + 50² + 150²)/4 = 12500")
case("single", [440], [25], [1], F(440), F(0), "one tone: centroid 440, spread 0")
case("unmatched", [100, 150, 300], [1, 81, 1], [1, 0, 3], F(200), F(10000),
     "the 150 Hz tone is left out: mean of 100 and 300 is 200, variance 100² = 10000")
case("zero_height", [100, 200, 900], [16, 16, 0], [1, 2, 9], F(150), F(2500),
     "the 900 Hz tone has no weight: mean 150, variance 50² = 2500")

err("none_matched", {"orders": [0, 0]}, "no tone has order >= 1")
err("matched_silent", {"heights": [0.0, 1.0], "orders": [1, 0]},
    "the matched tone's height is 0")
err("length_mismatch", {"orders": [1, 2, 3]}, "orders is longer than frequencies")
err("negative_height", {"heights": [1.0, -1.0]}, "heights must be non-negative")
err("negative_order", {"orders": [1, -2]}, "orders must be >= 0")
err("zero_tone", {"frequencies": [0.0, 200.0]}, "frequencies must be positive")

doc = {
    "schema": 1,
    "suite": "harmonic_centroid",
    "description": "Harmonic centroid and spread (conventions: Spectra, Harmonic centroid; "
    "ADR 0145).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "harmonic_centroid.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/harmonic_centroid.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
