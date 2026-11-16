"""Writes vectors/cases/spectral_crest.json in exact fractions, stdlib only.

The crest is the PSD's peak over its overlap-weighted mean across a band (conventions: Spectra,
Spectral crest factor; ADR 0125). Every case gives the peak and the mean worked by hand as
Fractions. The generator checks them against a Fraction recomputation and writes the crest and
its dB from them.

Run from the repo root: python vectors/generators/spectral_crest.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def peak_mean(freqs, psd, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    ws, ds = [], []
    for f_l, f_r, p in zip(left, right, psd):
        w = min(f_r, hi) - max(f_l, lo)
        if w > 0:
            ws.append(w)
            ds.append(F(p) * delta / (f_r - f_l))
    return max(ds), sum(w * d for w, d in zip(ws, ds)) / sum(ws)


def case(cid, args, peak, mean, why):
    assert peak_mean(args["frequencies"], args["psd"], args.get("band"), args.get("span")) == (
        peak, mean), cid
    cases.append({"id": f"spectral_crest.{cid}", "op": "spectral_crest", "args": args,
                  "expected": {"peak": float(peak), "mean": float(mean),
                               "crest": float(peak / mean),
                               "crest_db": 10 * (math.log10(peak) - math.log10(mean))},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_crest.{cid}", "op": "spectral_crest", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4}, F(2), F(2),
     "flat at 2: peak 2, mean 2, crest 1, 0 dB")
case("single_bin", {"frequencies": F4, "psd": [0.0, 5.0, 0.0, 0.0]}, F(5), F(5, 4),
     "one bin of 5 in four equal bins: mean 5/4, crest 4")
case("uneven", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0]}, F(4), F(5, 2),
     "peak 4, mean 10/4 = 5/2, crest 8/5")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 8.0], "band": [0.0, 2.25]},
     F(3), F(19, 9),
     "band [0, 2.25]: weights 1/2, 1, 3/4 on densities 1, 2, 3; mean (1/2 + 2 + 9/4) / (9/4) "
     "= 19/9; bin 3 does not overlap, so the peak is 3")
case("touching_bin_counts", {"frequencies": F4, "psd": [1.0, 1.0, 1.0, 9.0],
                             "band": [0.0, 2.75]}, F(9), F(19, 11),
     "band [0, 2.75]: weights 1/2, 1, 1, 1/4 on 1, 1, 1, 9; mean (1/2 + 1 + 1 + 9/4) / (11/4) "
     "= 19/11; bin 3 overlaps a quarter, so the peak is 9")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     F(4), F(2),
     "span (0, 3) halves bins 0 and 3, which keep power 2 at density 4: peak 4; mean "
     "(2 + 1 + 1 + 2) / 3 = 2")

err("band_reversed", {"frequencies": F4, "psd": [1.0] * 4, "band": [2.0, 1.0]},
    "band low must be below band high")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [-1.0, 3.0]},
    "band [-1, 3] leaves the spectrum [-0.5, 3.5]")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("negative_psd", {"frequencies": F4, "psd": [1.0, -1.0, 1.0, 1.0]},
    "psd must be non-negative")

doc = {
    "schema": 1,
    "suite": "spectral_crest",
    "description": "Spectral crest factor (conventions: Spectra, Spectral crest factor; ADR "
    "0125).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_crest.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_crest.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
