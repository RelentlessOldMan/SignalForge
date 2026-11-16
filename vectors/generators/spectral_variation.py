"""Writes vectors/cases/spectral_variation.json, stdlib only.

The variation is one minus the normalized correlation of two PSD frames' step densities over a
band (conventions: Spectra, Spectral variation; ADR 0131). The generator takes the correlation
squared as an exact Fraction and asserts it against each hand value. Only its square root is in
floating point.

Run from the repo root: python vectors/generators/spectral_variation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def correlation_squared(freqs, prev, cur, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    cross = sq0 = sq1 = F(0)
    for f_l, f_r, p0, p1 in zip(left, right, prev, cur):
        a, b = max(f_l, lo), min(f_r, hi)
        if b > a:
            d0, d1 = F(p0) * delta / (f_r - f_l), F(p1) * delta / (f_r - f_l)
            cross += d0 * d1 * (b - a)
            sq0 += d0 * d0 * (b - a)
            sq1 += d1 * d1 * (b - a)
    return cross * cross / (sq0 * sq1)


def case(cid, args, want_sq, why):
    got = correlation_squared(args["frequencies"], args["previous"], args["current"],
                              args.get("band"), args.get("span"))
    assert got == want_sq, (cid, got, want_sq)
    cases.append({"id": f"spectral_variation.{cid}", "op": "spectral_variation", "args": args,
                  "expected": 1.0 - math.sqrt(want_sq), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_variation.{cid}", "op": "spectral_variation", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
ONES = [1.0] * 4
UP = [1.0, 2.0, 1.0, 1.0]
case("identical", {"frequencies": F4, "previous": UP, "current": UP}, F(1),
     "identical frames: correlation 1, variation 0")
case("doubled", {"frequencies": F4, "previous": UP, "current": [2 * v for v in UP]}, F(1),
     "a frame against its double: correlation 1, variation 0")
case("disjoint", {"frequencies": F4, "previous": [1.0, 0.0, 0.0, 0.0],
                  "current": [0.0, 0.0, 0.0, 1.0]}, F(0),
     "frames sharing no bin: correlation 0, variation 1")
case("overlap", {"frequencies": F4, "previous": [1.0, 1.0, 0.0, 0.0],
                 "current": [0.0, 1.0, 1.0, 0.0]}, F(1, 4),
     "one shared bin: correlation 1 / sqrt(2 x 2) = 1/2, variation 1/2")
case("uneven", {"frequencies": F4, "previous": UP, "current": ONES}, F(25, 28),
     "cross 5, norms^2 7 and 4: correlation^2 25/28")
case("cut_band", {"frequencies": F4, "previous": ONES, "current": [3.0, 1.0, 1.0, 1.0],
                  "band": [0.25, 3.0]}, F(169, 209),
     "band [0.25, 3], widths 1/4, 1, 1, 1/2: cross 13/4, norms^2 11/4 and 19/4")
case("span_clipped", {"frequencies": F4, "previous": ONES, "current": [2.0, 1.0, 1.0, 1.0],
                      "span": [0.0, 3.0]}, F(8, 9),
     "span (0, 3), outer bins halved: densities 2, 1, 1, 2 and 4, 1, 1, 2; cross 8, "
     "norms^2 6 and 12")

err("no_power", {"frequencies": F4, "previous": ONES, "current": [0.0] * 4},
    "each frame needs power in the band")
err("length_mismatch", {"frequencies": F4, "previous": [1.0, 1.0, 1.0], "current": ONES},
    "frequencies and psd must be the same length")
err("band_outside", {"frequencies": F4, "previous": ONES, "current": ONES, "band": [-1.0, 3.0]},
    "band [-1, 3] leaves the spectrum [-0.5, 3.5]")

doc = {
    "schema": 1,
    "suite": "spectral_variation",
    "description": "Spectral variation (conventions: Spectra, Spectral variation; ADR 0131).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_variation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_variation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
