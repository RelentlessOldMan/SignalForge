"""Writes vectors/cases/acpr_rrc.json by hand arithmetic, using only the Python standard library.

It does not import NumPy or SignalForge. Every PSD is a short list of bins, and every expected
power is a sum of bin powers times the raised-cosine weight G of ADR 0111, written out term by
term; where the weights pair up (cos t + cos(pi - t) = 0) the sum is the symbol rate exactly.

Run from the repo root: python vectors/generators/acpr_rrc.py [--check]
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
    return {"id": case_id, "op": "acpr_rrc", "args": args,
            "expected": {"main_power": main, "lower_power": lower, "upper_power": upper,
                         "lower_dbc": [db(v / main) for v in lower],
                         "upper_dbc": [db(v / main) for v in upper]},
            "tol": TOL, "source": src}


def err(case_id, args, why):
    return {"id": case_id, "op": "acpr_rrc", "args": args, "error": "invalid_argument",
            "source": why}


# Two-sided, bins at -16 ... 15 Hz, 1 Hz wide (edges -16.5 and 15.5).
f2 = [float(k) for k in range(-16, 16)]
flat = [2.0] * len(f2)
# A step: 1 inside the main channel, 0.01 under the upper adjacent, 0.001 under the lower; the
# bins at +-3 are where G is 0 for every channel (R = 4, alpha = 0.5: support +-3), so the 5
# there is never counted.
step_level = {k: 1.0 for k in range(-2, 3)}
step_level.update({k: 0.01 for k in range(4, 9)})
step_level.update({k: 0.001 for k in range(-8, -3)})
step_level.update({-3: 5.0, 3: 5.0})
step = [step_level.get(k, 0.0) for k in range(-16, 16)]
# Lines: 1 at 0 Hz, 3 at 7 Hz, 2 at -6 Hz.
lines = [{0: 1.0, 7: 3.0, -6: 2.0}.get(k, 0.0) for k in range(-16, 16)]
# One-sided, bins at 0 ... 16 Hz, span (0, 16): bins 0 and 16 are half bins, but a bin's power
# is still psd * delta (ADR 0019's bins).
f1 = [float(k) for k in range(17)]
ones = [1.0] * 17

# Centre 0.25 on 1 Hz bins: the taper bins sit at t = pi/8, 3pi/8, 5pi/8, 7pi/8, and
# cos(pi/8) + cos(7pi/8) = cos(3pi/8) + cos(5pi/8) = 0.
off_bins = 2.0 * (1 + 1 + sum(0.5 * (1 + math.cos(j * math.pi / 8)) for j in (1, 3, 5, 7)))
r2 = math.sqrt(2) / 2

cases = [
    case("acpr_rrc.flat_on_bins", {"frequencies": f2, "psd": flat, "center": 0.0,
                                   "symbol_rate": 4.0, "alpha": 0.5, "offsets": [6.0]},
         8.0, [8.0], [8.0],
         "by hand: R = 4, alpha = 0.5, so G = 1 to |x| = 1, then 0.5(1 + cos(pi(|x| - 1)/2)) "
         "to 3; on whole bins G = 1 at x = 0, +-1 and 0.5 at +-2 (cos(pi/2) = 0), 0 at +-3; "
         "the sum 4 times psd 2 is 8 in every channel, psd times R"),
    case("acpr_rrc.flat_off_bins", {"frequencies": f2, "psd": flat, "center": 0.25,
                                    "symbol_rate": 4.0, "alpha": 0.5, "offsets": [6.0]},
         off_bins, [off_bins], [off_bins],
         "by hand: centre 0.25 puts bins at |x| = 0.25, 0.75 (G = 1), 1.25, 1.75, 2.25, 2.75 "
         "(G = 0.5(1 + cos t), t = pi/8, 3pi/8, 5pi/8, 7pi/8, whose cosines cancel in pairs) "
         "and 3.25 (G = 0): the sum is 2 + 0.5 x 4 = 4 = R, times psd 2; the adjacent channels "
         "at -5.75 and 6.25 sit the same way on the bins"),
    case("acpr_rrc.step", {"frequencies": f2, "psd": step, "center": 0.0, "symbol_rate": 4.0,
                           "alpha": 0.5, "offsets": [6.0]},
         4.0, [4.0 * 0.001], [4.0 * 0.01],
         "by hand: each channel's nonzero weights (1, 1, 1, 0.5, 0.5 on its five middle bins, "
         "sum 4) cover one level: 1 in the main, 0.001 under the lower at -6, 0.01 under the "
         "upper at 6; the bins at -3 and 3 hold 5 but sit where every channel's G is 0"),
    case("acpr_rrc.taper", {"frequencies": f2, "psd": lines, "center": 0.0, "symbol_rate": 4.0,
                            "alpha": 0.5, "offsets": [4.5]},
         1.0, [2.0 * 0.5 * (1 + r2)], [3.0 * 0.5 * (1 - r2)],
         "by hand: the main channel holds only the line at 0 (G = 1); the lower channel at "
         "-4.5 sees the line 2 at -6, |x| = 1.5, G = 0.5(1 + cos(pi/4)); the upper at 4.5 sees "
         "the line 3 at 7, |x| = 2.5, G = 0.5(1 + cos(3pi/4)); the line at 0 is 4.5 from each, "
         "outside the support 3"),
    case("acpr_rrc.alpha_one_one_sided", {"frequencies": f1, "psd": ones, "center": 8.0,
                                          "symbol_rate": 2.0, "alpha": 1.0,
                                          "offsets": [4.0, 6.0], "span": [0.0, 16.0]},
         2.0, [2.0, 2.0], [2.0, 2.0],
         "by hand: R = 2, alpha = 1, so G = 0.5(1 + cos(pi|x|/2)) to |x| = 2: 1 at the centre "
         "bin, 0.5 at +-1, 0 at +-2, sum 2 = R; offset 6 puts the lower support [0, 4] and the "
         "upper [12, 16] exactly on the spectrum's edges, which is allowed"),
    err("acpr_rrc.support_past_the_edge", {"frequencies": f1, "psd": ones, "center": 8.0,
                                           "symbol_rate": 2.0, "alpha": 1.0, "offsets": [7.0],
                                           "span": [0.0, 16.0]},
        "the lower channel's support [-1, 3] starts below the clipped spectrum's 0"),
    err("acpr_rrc.main_empty", {"frequencies": f2, "psd": lines, "center": 12.0,
                                "symbol_rate": 2.0, "alpha": 0.5, "offsets": [1.0]},
        "the main channel at 12 Hz (support 10.5 to 13.5) holds no power"),
    err("acpr_rrc.alpha_zero", {"frequencies": f2, "psd": flat, "center": 0.0,
                                "symbol_rate": 4.0, "alpha": 0.0, "offsets": [6.0]},
        "alpha must be > 0 (a rectangle is acpr's job)"),
    err("acpr_rrc.alpha_above_one", {"frequencies": f2, "psd": flat, "center": 0.0,
                                     "symbol_rate": 4.0, "alpha": 1.5, "offsets": [6.0]},
        "alpha must be <= 1"),
    err("acpr_rrc.alpha_nan", {"frequencies": f2, "psd": flat, "center": 0.0,
                               "symbol_rate": 4.0, "alpha": "nan", "offsets": [6.0]},
        "alpha must be finite"),
    err("acpr_rrc.symbol_rate_zero", {"frequencies": f2, "psd": flat, "center": 0.0,
                                      "symbol_rate": 0.0, "alpha": 0.5, "offsets": [6.0]},
        "symbol_rate > 0 required"),
    err("acpr_rrc.symbol_rate_inf", {"frequencies": f2, "psd": flat, "center": 0.0,
                                     "symbol_rate": "inf", "alpha": 0.5, "offsets": [6.0]},
        "symbol_rate must be finite"),
    err("acpr_rrc.no_offsets", {"frequencies": f2, "psd": flat, "center": 0.0,
                                "symbol_rate": 4.0, "alpha": 0.5, "offsets": []},
        "at least one offset required"),
    err("acpr_rrc.offset_negative", {"frequencies": f2, "psd": flat, "center": 0.0,
                                     "symbol_rate": 4.0, "alpha": 0.5, "offsets": [-6.0]},
        "offsets must be > 0"),
    err("acpr_rrc.center_nan", {"frequencies": f2, "psd": flat, "center": "nan",
                                "symbol_rate": 4.0, "alpha": 0.5, "offsets": [6.0]},
        "center must be finite"),
]

doc = {
    "schema": 1,
    "suite": "acpr_rrc",
    "description": "ACPR through a root-raised-cosine channel filter (conventions: Spectra, "
                   "ACPR; ADR 0111).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "acpr_rrc.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/acpr_rrc.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
