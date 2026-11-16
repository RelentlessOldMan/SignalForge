"""Writes vectors/cases/noise_power_ratio.json by hand arithmetic, using only the Python standard
library.

It does not import NumPy or SignalForge. Every PSD here is a short list of piecewise-constant bins,
and every expected density is written out as the bins (or parts of bins) a region covers over the
region's width, as conventions: Spectra (channel power, noise power ratio) define it (ADR 0118).

Run from the repo root: python vectors/generators/noise_power_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

OP = "noise_power_ratio"
TOL = {"abs": 1e-12, "rel": 1e-12}


def case(cid, args, loaded, notch, src):
    npr = "inf" if notch == 0 else 10 * (math.log10(loaded) - math.log10(notch))
    return {"id": f"{OP}.{cid}", "op": OP, "args": args,
            "expected": {"loaded_density": loaded, "notch_density": notch, "npr_db": npr},
            "tol": TOL, "source": src}


def err(cid, args, why):
    return {"id": f"{OP}.{cid}", "op": OP, "args": args, "error": "invalid_argument",
            "source": why}


# Two-sided, bins at -8 ... 7 Hz, 1 Hz wide (edges at k +- 0.5).
f2 = [float(k) for k in range(-8, 8)]
level = {-6: 1.0, -5: 1.0, -4: 1.0, -3: 1.0, -2: 1.0, -1: 2.0, 0: 1e-3, 1: 4e-3, 2: 2.0, 3: 1.0,
         4: 1.0, 5: 1.0, 6: 1.0}
p2 = [level.get(k, 0.0) for k in range(-8, 8)]
# One-sided, bins at 0 ... 8 Hz (fs = 16), span (0, 8): bins 0 and 8 are half bins.
f1 = [float(k) for k in range(9)]
p1 = [0.5, 0.5, 0.5, 0.5, 0.01, 0.5, 0.5, 0.5, 0.5]
S = {"span": [0.0, 8.0]}

cases = [
    case("whole_bins", {"frequencies": f2, "psd": p2, "band": [-6.5, 6.5], "notch": [-0.5, 0.5]},
         (5 * 1.0 + 2.0 + 4e-3 + 2.0 + 4 * 1.0) / 12, 1e-3 / 1,
         "by hand: band [-6.5, 6.5] is bins -6..6; notch [-0.5, 0.5] is bin 0 (0.001); the loaded "
         "region is bins -6..-1 (5 x 1 + 2) and 1..6 (0.004 + 2 + 4 x 1), 12 Hz wide"),
    case("partial_bins", {"frequencies": f2, "psd": p2, "band": [-4.25, 4.5], "notch": [-0.25, 1.0]},
         (0.75 * 1.0 + 2 * 1.0 + 2.0 + 0.25 * 1e-3 + 0.5 * 4e-3 + 2.0 + 2 * 1.0) / (4.0 + 3.5),
         (0.75 * 1e-3 + 0.5 * 4e-3) / 1.25,
         "by hand: lower part [-4.25, -0.25] takes 3/4 of bin -4, bins -3..-1 (1, 1, 2) and 1/4 of "
         "bin 0; notch [-0.25, 1] takes 3/4 of bin 0 and half of bin 1; upper part [1, 4.5] takes "
         "half of bin 1 and bins 2..4 (2, 1, 1); widths 4 + 3.5 and 1.25"),
    case("one_sided_span", {"frequencies": f1, "psd": p1, "band": [0.0, 8.0], "notch": [3.5, 4.5],
                            **S},
         (0.5 + 3 * 0.5 + 3 * 0.5 + 0.5) / 7, 0.01,
         "by hand: bins of 0.5 everywhere but bin 4 (0.01), each holding psd x 1 Hz; bin 0, "
         "clipped to [0, 0.5], and bin 8, clipped to [7.5, 8], keep their whole power; the loaded "
         "parts [0, 3.5] and [4.5, 8] hold 2 each over 7 Hz; the notch is bin 4"),
    case("empty_notch", {"frequencies": f1, "psd": [0.5, 0.5, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5],
                         "band": [0.5, 7.5], "notch": [3.5, 4.5], **S},
         0.5, 0.0, "by hand: the notch (bin 4) is empty, so the ratio is +inf"),
    err("notch_below_band", {"frequencies": f2, "psd": p2, "band": [-2.0, 2.0],
                             "notch": [-3.0, -1.0]}, "the notch starts below the band"),
    err("notch_on_band_edge", {"frequencies": f2, "psd": p2, "band": [-2.0, 2.0],
                               "notch": [-1.0, 2.0]}, "notch high = band high leaves no upper part"),
    err("notch_reversed", {"frequencies": f2, "psd": p2, "band": [-2.0, 2.0], "notch": [1.0, -1.0]},
        "notch low must be below notch high"),
    err("band_past_the_end", {"frequencies": f2, "psd": p2, "band": [-6.0, 8.0],
                              "notch": [-0.5, 0.5]}, "the band runs past the last bin's edge, 7.5"),
    err("loaded_empty", {"frequencies": f2, "psd": [0.0] * 16, "band": [-2.0, 2.0],
                         "notch": [-0.5, 0.5]}, "the loaded band has no power"),
    err("edge_nan", {"frequencies": f2, "psd": p2, "band": ["nan", 2.0], "notch": [-0.5, 0.5]},
        "band edges must be finite"),
    err("psd_negative", {"frequencies": f2, "psd": [-1.0] + p2[1:], "band": [-6.5, 6.5],
                         "notch": [-0.5, 0.5]}, "psd must be non-negative"),
]

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Noise power ratio from a PSD (conventions: Spectra, Noise power ratio; "
    "ADR 0118).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
