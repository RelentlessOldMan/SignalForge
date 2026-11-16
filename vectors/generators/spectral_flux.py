"""Writes vectors/cases/spectral_flux.json in exact fractions, stdlib only.

The flux is the L2 distance between two PSD frames' step densities over a band (conventions:
Spectra, Spectral flux; ADR 0129). The generator takes the squared flux as an exact Fraction and
asserts it against each hand value. Only the final square root is in floating point.

Run from the repo root: python vectors/generators/spectral_flux.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def flux_squared(freqs, prev, cur, band=None, span=None, normalize=True, rectify=True):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    frames = []
    for psd in (prev, cur):
        ps = []
        for f_l, f_r, p in zip(left, right, psd):
            a, b = max(f_l, lo), min(f_r, hi)
            if b > a:
                ps.append((b - a, F(p) * delta / (f_r - f_l)))
        if normalize:
            power = sum(w * d for w, d in ps)
            ps = [(w, d / power) for w, d in ps]
        frames.append(ps)
    total = F(0)
    for (w, d0), (_, d1) in zip(*frames):
        step = d1 - d0
        if rectify:
            step = max(step, F(0))
        total += step * step * w
    return total


def case(cid, args, want_sq, why):
    got = flux_squared(args["frequencies"], args["previous"], args["current"], args.get("band"),
                       args.get("span"), args.get("normalize", True), args.get("rectify", True))
    assert got == want_sq, (cid, got, want_sq)
    cases.append({"id": f"spectral_flux.{cid}", "op": "spectral_flux", "args": args,
                  "expected": math.sqrt(want_sq), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_flux.{cid}", "op": "spectral_flux", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
ONES = [1.0] * 4
UP = [1.0, 2.0, 1.0, 1.0]
case("identical", {"frequencies": F4, "previous": UP, "current": UP}, F(0),
     "identical frames: flux 0")
case("doubled_normalized", {"frequencies": F4, "previous": UP, "current": [2 * v for v in UP]},
     F(0), "a frame against its double, normalized: the same shape, flux 0")
case("doubled_raw", {"frequencies": F4, "previous": ONES, "current": [2.0] * 4,
                     "normalize": False}, F(4),
     "flat 1 to flat 2, not normalized: a rise of 1 over a width of 4, flux^2 = 4, flux 2")
case("one_bin_raw", {"frequencies": F4, "previous": ONES, "current": UP, "normalize": False},
     F(1), "bin 1 rises by 1 over width 1, not normalized: flux 1")
case("one_bin_normalized", {"frequencies": F4, "previous": ONES, "current": UP}, F(9, 400),
     "normalized: 1/4 each, then 1/5, 2/5, 1/5, 1/5; the only rise is 3/20, flux 3/20")
case("one_bin_both_ways", {"frequencies": F4, "previous": ONES, "current": UP,
                           "rectify": False}, F(12, 400),
     "normalized, not rectified: steps -1/20, 3/20, -1/20, -1/20; flux^2 = 12/400")
case("falls_only", {"frequencies": F4, "previous": UP, "current": ONES, "normalize": False},
     F(0), "bin 1 falls, nothing rises, rectified and not normalized: flux 0")
case("falls_unrectified", {"frequencies": F4, "previous": UP, "current": ONES,
                           "normalize": False, "rectify": False}, F(1),
     "bin 1 falls by 1, not rectified: flux 1")
case("cut_band", {"frequencies": F4, "previous": ONES, "current": [3.0, 1.0, 1.0, 1.0],
                  "band": [0.25, 3.0], "normalize": False}, F(4) * F(1, 4),
     "band [0.25, 3] keeps a quarter of bin 0, which rises by 2: flux^2 = 4 x 1/4 = 1")
case("span_clipped", {"frequencies": F4, "previous": ONES, "current": [2.0, 1.0, 1.0, 1.0],
                      "span": [0.0, 3.0], "normalize": False}, F(2) ** 2 * F(1, 2),
     "span (0, 3) halves bin 0, doubling its density: 2 to 4, a rise of 2 over width 1/2, "
     "flux^2 = 2")

err("no_power_normalized", {"frequencies": F4, "previous": [0.0] * 4, "current": ONES},
    "with normalize, each frame needs power in the band")
err("length_mismatch", {"frequencies": F4, "previous": ONES, "current": [1.0, 1.0, 1.0]},
    "frequencies and psd must be the same length")
err("negative", {"frequencies": F4, "previous": ONES, "current": [1.0, -1.0, 1.0, 1.0]},
    "psd must be non-negative")

doc = {
    "schema": 1,
    "suite": "spectral_flux",
    "description": "Spectral flux (conventions: Spectra, Spectral flux; ADR 0129).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_flux.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_flux.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
