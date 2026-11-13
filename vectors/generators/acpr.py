"""Writes vectors/cases/acpr.json by hand arithmetic, using only the Python standard library.

It does not import NumPy or SignalForge. Every PSD here is a short list of piecewise-constant bins,
and every expected power is written out as the sum of the bins (or parts of bins) a channel covers,
as conventions: Spectra (channel power, ACPR) define it.

Run from the repo root: python vectors/generators/acpr.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}


def db(x):
    return 10 * math.log10(x) if x > 0 else "-inf"


def case(case_id, args, main, lower, upper, src):
    return {"id": case_id, "op": "acpr", "args": args,
            "expected": {"main_power": main, "lower_power": lower, "upper_power": upper,
                         "lower_dbc": [db(v / main) for v in lower],
                         "upper_dbc": [db(v / main) for v in upper]},
            "tol": TOL, "source": src}


def err(case_id, args, why):
    return {"id": case_id, "op": "acpr", "args": args, "error": "invalid_argument", "source": why}


# Two-sided, bins at -8 ... 7 Hz, 1 Hz wide (edges at k +- 0.5).
f2 = [float(k) for k in range(-8, 8)]
level = {-7: 3e-4, -6: 3e-4, -5: 3e-4, -4: 3e-3, -3: 3e-3, -2: 3e-3, -1: 1.0, 0: 1.0, 1: 1.0,
         2: 0.03, 3: 0.03, 4: 0.03}
p2 = [level.get(k, 0.0) for k in range(-8, 8)]
# One-sided, bins at 0 ... 8 Hz (fs = 16), span (0, 8): bins 0 and 8 are half bins.
f1 = [float(k) for k in range(9)]
p1 = [0.5, 0.25, 0.125, 2.0, 4.0, 2.0, 0.0625, 0.03125, 0.5]

cases = [
    case("acpr.whole_bins", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                             "offsets": [3.0, 6.0]},
         3.0, [3 * 3e-3, 3 * 3e-4], [3 * 0.03, 0.0],
         "by hand: main [-1.5, 1.5] is bins -1..1, 3 x 1; offset 3: lower [-4.5, -1.5] is bins "
         "-4..-2, 3 x 0.003, upper [1.5, 4.5] bins 2..4, 3 x 0.03; offset 6: lower bins -7..-5, "
         "3 x 0.0003, upper bins 5..7, empty (-inf dBc)"),
    case("acpr.partial_bins", {"frequencies": f2, "psd": p2, "center": 0.25, "bandwidth": 2.0,
                               "offsets": [2.5]},
         0.25 + 1.0 + 0.75, [0.75 * 3e-3 + 3e-3 + 0.25 * 1.0], [(0.75 + 1 + 0.25) * 0.03],
         "by hand: main [-0.75, 1.25] takes 1/4 of bin -1, bin 0 and 3/4 of bin 1; lower "
         "[-3.25, -1.25] takes 3/4 of bin -3, bin -2 and 1/4 of bin -1; upper [1.75, 3.75] takes "
         "3/4 of bin 2, bin 3 and 1/4 of bin 4"),
    case("acpr.narrow_adjacent", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                                  "offsets": [3.0], "adjacent_bandwidth": 1.0},
         3.0, [3e-3], [0.03],
         "by hand: adjacent channels 1 Hz wide at -3 and 3 Hz are exactly bins -3 and 3"),
    case("acpr.one_sided_span", {"frequencies": f1, "psd": p1, "center": 4.0, "bandwidth": 2.0,
                                 "offsets": [3.0], "span": [0.0, 8.0]},
         0.5 * 2.0 + 4.0 + 0.5 * 2.0, [0.5 + 0.25 + 0.5 * 0.125],
         [0.5 * 0.0625 + 0.03125 + 0.5],
         "by hand: main [3, 5] takes half of bins 3 and 5 and bin 4; lower [0, 2] takes bin 0 (its "
         "clipped width [0, 0.5] is inside, so all of its power), bin 1 and half of bin 2; upper "
         "[6, 8] half of bin 6, bin 7 and all of the clipped bin 8"),
    case("acpr.edge_after_rounding", {"frequencies": f1, "psd": p1, "center": 0.3,
                                      "bandwidth": 0.4, "offsets": [0.1], "span": [0.0, 8.0]},
         0.4 * 0.5 / 0.5, [0.4 * 0.5 / 0.5], [0.3 * 0.5 / 0.5 + 0.1 * 0.25],
         "by hand: bin 0 holds 0.5 over its clipped width [0, 0.5]; main [0.1, 0.5] takes 0.4 of it; "
         "lower [0, 0.4] starts exactly at the spectrum's edge (0.3 - 0.1 - 0.2 rounds a hair below "
         "0, inside the 1e-9-bin slack) and takes 0.4 of it; upper [0.2, 0.6] takes 0.3 of bin 0 "
         "and 0.1 of bin 1 (0.25)"),
    err("acpr.channel_past_the_end", {"frequencies": f2, "psd": p2, "center": 0.0,
                                      "bandwidth": 3.0, "offsets": [7.0]},
        "the upper channel [5.5, 8.5] runs past the last bin's edge, 7.5"),
    err("acpr.below_zero_one_sided", {"frequencies": f1, "psd": p1, "center": 2.0,
                                      "bandwidth": 2.0, "offsets": [3.0], "span": [0.0, 8.0]},
        "the lower channel [-2, 0] is below the clipped spectrum, which starts at 0"),
    err("acpr.main_empty", {"frequencies": f2, "psd": p2, "center": 6.0, "bandwidth": 1.0,
                            "offsets": [1.0]}, "the main channel (bin 6) has no power"),
    err("acpr.bandwidth_zero", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 0.0,
                                "offsets": [3.0]}, "bandwidth > 0 required"),
    err("acpr.bandwidth_nan", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": "nan",
                               "offsets": [3.0]}, "bandwidth must be finite"),
    err("acpr.adjacent_negative", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                                   "offsets": [3.0], "adjacent_bandwidth": -1.0},
        "adjacent_bandwidth > 0 required"),
    err("acpr.no_offsets", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                            "offsets": []}, "at least one offset required"),
    err("acpr.offset_zero", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                             "offsets": [3.0, 0.0]}, "offsets must be > 0"),
    err("acpr.offset_inf", {"frequencies": f2, "psd": p2, "center": 0.0, "bandwidth": 3.0,
                            "offsets": ["inf"]}, "offsets must be finite"),
    err("acpr.center_nan", {"frequencies": f2, "psd": p2, "center": "nan", "bandwidth": 3.0,
                            "offsets": [3.0]}, "center must be finite"),
    err("acpr.psd_negative", {"frequencies": f2, "psd": [-1.0] + p2[1:], "center": 0.0,
                              "bandwidth": 3.0, "offsets": [3.0]}, "psd must be non-negative"),
]

doc = {
    "schema": 1,
    "suite": "acpr",
    "description": "Adjacent channel power ratio from a PSD (conventions: Spectra, ACPR).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "acpr.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/acpr.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
