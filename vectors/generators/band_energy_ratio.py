"""Writes vectors/cases/band_energy_ratio.json, stdlib only.

The low and high powers are the band's step density integrated below and above the split
(conventions: Spectra, Band energy ratio; ADR 0134). The generator computes both in exact
Fractions and asserts each against a hand value. Only the dB is taken in floating point.

Run from the repo root: python vectors/generators/band_energy_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def powers(freqs, psd, split, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    s = F(split)
    low = high = F(0)
    for f_l, f_r, p in zip(left, right, psd):
        d = F(p) * delta / (f_r - f_l)
        low += d * max(min(f_r, s) - max(f_l, lo), F(0))
        high += d * max(min(f_r, hi) - max(f_l, s), F(0))
    return low, high


def case(cid, args, low, high, why):
    got = powers(args["frequencies"], args["psd"], args["split"], args.get("band"),
                 args.get("span"))
    assert got == (low, high), (cid, got, low, high)
    if low == 0:
        ratio, db = "inf", "inf"
    elif high == 0:
        ratio, db = 0.0, "-inf"
    else:
        ratio, db = float(high / low), 10 * math.log10(high / low)
    cases.append({"id": f"band_energy_ratio.{cid}", "op": "band_energy_ratio", "args": args,
                  "expected": {"low": float(low), "high": float(high), "ratio": ratio,
                               "ratio_db": db},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"band_energy_ratio.{cid}", "op": "band_energy_ratio", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
RAMP = [1.0, 2.0, 3.0, 4.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4, "split": 1.5}, F(4), F(4),
     "flat split in the middle: 4 and 4, ratio 1, 0 dB")
case("ramp_between_bins", {"frequencies": F4, "psd": RAMP, "split": 1.5}, F(3), F(7),
     "split at the edge between bins 1 and 2: 1 + 2 and 3 + 4")
case("ramp_inside_bin", {"frequencies": F4, "psd": RAMP, "split": 2.0}, F(9, 2), F(11, 2),
     "split at bin 2's center: 1 + 2 + 3/2 and 3/2 + 4")
case("spaced", {"frequencies": [10.0, 30.0, 50.0, 70.0], "psd": RAMP, "split": 40.0},
     F(60), F(140), "the ramp on 20 Hz bins split at 40 Hz: 20 x 3 and 20 x 7")
case("cut_band", {"frequencies": F4, "psd": RAMP, "split": 1.0, "band": [0.25, 3.0]},
     F(5, 4), F(6), "band [0.25, 3], split 1: 1 x 1/4 + 2 x 1/2 and 2 x 1/2 + 3 + 4 x 1/2")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "split": 0.25,
                      "span": [0.0, 3.0]}, F(1), F(5),
     "span (0, 3): bin 0 is [0, 1/2] at density 4; split 1/4: 4 x 1/4 and 4 x 1/4 + 1 + 1 + "
     "4 x 1/2")
case("no_low_power", {"frequencies": F4, "psd": [0.0, 0.0, 3.0, 4.0], "split": 1.5}, F(0),
     F(7), "nothing below the split: ratio and dB +inf")
case("no_high_power", {"frequencies": F4, "psd": [1.0, 2.0, 0.0, 0.0], "split": 1.5}, F(3),
     F(0), "nothing above the split: ratio 0, dB -inf")

err("split_at_edge", {"frequencies": F4, "psd": RAMP, "split": -0.5},
    "split must be strictly inside the band")
err("split_outside_band", {"frequencies": F4, "psd": RAMP, "split": 3.2, "band": [0.0, 3.0]},
    "split 3.2 is above the band [0, 3]")
err("no_power", {"frequencies": F4, "psd": [0.0] * 4, "split": 1.5}, "the band has no power")
err("band_outside", {"frequencies": F4, "psd": RAMP, "split": 1.5, "band": [0.0, 4.0]},
    "band [0, 4] leaves the spectrum [-0.5, 3.5]")

doc = {
    "schema": 1,
    "suite": "band_energy_ratio",
    "description": "Band energy ratio (conventions: Spectra, Band energy ratio; ADR 0134).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "band_energy_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/band_energy_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
