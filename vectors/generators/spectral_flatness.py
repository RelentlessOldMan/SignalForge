"""Writes vectors/cases/spectral_flatness.json from hand-worked closed forms, stdlib only.

Each case is a short PSD whose density-weighted logs come out as small powers of 2, so the
geometric mean is written in closed form (for example 4**(3/4) = 2**1.5) and the arithmetic mean
is a short fraction (conventions: Spectra, Spectral flatness; ADR 0120).

Run from the repo root: python vectors/generators/spectral_flatness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, args, geo, arith, why):
    flat = geo / arith
    db = 10 * (math.log10(geo) - math.log10(arith)) if geo > 0 else "-inf"
    cases.append({"id": f"spectral_flatness.{cid}", "op": "spectral_flatness", "args": args,
                  "expected": {"geometric_mean": geo, "arithmetic_mean": arith,
                               "flatness": flat, "flatness_db": db},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_flatness.{cid}", "op": "spectral_flatness", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [2.0, 2.0, 2.0, 2.0]}, 2.0, 2.0,
     "by hand: a constant density 2; both means 2, flatness 1, 0 dB")
case("two_level", {"frequencies": [0.0, 1.0], "psd": [1.0, 4.0]}, 2.0, 2.5,
     "by hand: G = sqrt(1 x 4) = 2, A = 5/2, flatness 0.8")
case("three_level", {"frequencies": [0.0, 1.0, 2.0], "psd": [1.0, 4.0, 16.0]}, 4.0, 7.0,
     "by hand: G = (1 x 4 x 16)^(1/3) = 4, A = 21/3 = 7")
case("cut_bins", {"frequencies": F4, "psd": [1.0, 4.0, 4.0, 1.0], "band": [0.0, 2.0]},
     2 ** 1.5, 3.25,
     "by hand: band [0, 2] overlaps bins 0, 1, 2 by 0.5, 1, 0.5 (W = 2); ln G = (0.5 ln 1 + "
     "1.5 ln 4) / 2, G = 4^(3/4) = 2^1.5; A = (0.5 + 4 + 2) / 2 = 3.25")
case("zero_bin", {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, 4.0, 4.0]}, 0.0, 8 / 3,
     "by hand: a zero bin inside makes G = 0, flatness 0, -inf dB; A = 8/3")
case("zero_bin_outside_band", {"frequencies": F4, "psd": [0.0, 1.0, 4.0, 0.0],
                               "band": [0.5, 2.5]}, 2.0, 2.5,
     "by hand: band [0.5, 2.5] is exactly bins 1 and 2; the zero bins only touch its edges, "
     "weight 0, so G = sqrt(1 x 4) = 2, A = 5/2")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     4 ** (1 / 3), 2.0,
     "by hand: span (0, 3) halves bins 0 and 3, which keep their power 2, so density 4 over "
     "width 0.5; W = 3, ln G = (0.5 ln 4 + 0.5 ln 4) / 3, G = 4^(1/3); A = (2 + 1 + 1 + 2) / 3 = 2")

err("band_reversed", {"frequencies": F4, "psd": [1.0] * 4, "band": [2.0, 1.0]},
    "band low must be below band high")
err("band_empty", {"frequencies": F4, "psd": [1.0] * 4, "band": [1.0, 1.0]},
    "band low must be below band high")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 4.0]},
    "band [0, 4] leaves the spectrum [-0.5, 3.5]")
err("band_inf", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, "inf"]},
    "band edges must be finite")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 0.0, 1.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("negative_psd", {"frequencies": F4, "psd": [1.0, -1.0, 1.0, 1.0]},
    "psd must be non-negative")

doc = {
    "schema": 1,
    "suite": "spectral_flatness",
    "description": "Spectral flatness (conventions: Spectra, Spectral flatness; ADR 0120).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_flatness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_flatness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
