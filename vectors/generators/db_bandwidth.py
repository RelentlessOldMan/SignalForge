"""Writes vectors/cases/db_bandwidth.json from hand-worked crossings, stdlib only.

The drops are 10 log10 2 dB and 10 dB, so the threshold is exactly half or a tenth of the peak
(10**(-drop/10) rounds by an ulp, which moves no edge by more than that: the edge is continuous
in the threshold, even where a bin sits on it). Each edge is the linear-in-power crossing worked
with Fractions (conventions: Spectra, x dB bandwidth; ADR 0122).

Run from the repo root: python vectors/generators/db_bandwidth.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
HALF = 10 * math.log10(2)
cases = []


def crossing(f_out, p_out, f_in, p_in, t):
    """The point between an outer bin at or below t and its inner neighbour above t."""
    return F(f_out) + (t - F(p_out)) / (F(p_in) - F(p_out)) * (F(f_in) - F(f_out))


def case(cid, args, peak_i, lower, upper, why):
    f = args["frequencies"]
    cases.append({"id": f"db_bandwidth.{cid}", "op": "db_bandwidth", "args": args,
                  "expected": {"peak_frequency": f[peak_i], "peak_psd": args["psd"][peak_i],
                               "lower": float(lower), "upper": float(upper),
                               "bandwidth": float(upper - lower)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"db_bandwidth.{cid}", "op": "db_bandwidth", "args": args,
                  "error": "invalid_argument", "source": why})


F7 = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
case("symmetric", {"frequencies": F7, "psd": [0.0, 2.0, 6.0, 8.0, 6.0, 2.0, 0.0],
                   "drop_db": HALF}, 3, crossing(1, 2, 2, 6, 4), crossing(5, 2, 4, 6, 4),
     "peak 8 at 3 Hz, threshold 4: lower between 1 (2) and 2 (6) at 1.5; upper at 4.5")
FA = [10.0, 10.5, 11.0, 11.5, 12.0]
case("asymmetric", {"frequencies": FA, "psd": [1.0, 10.0, 8.0, 3.0, 0.0], "drop_db": HALF},
     1, crossing(10, 1, 10.5, 10, 5), crossing(11.5, 3, 11, 8, 5),
     "peak 10 at 10.5 Hz, threshold 5: lower 10 + (4/9) x 0.5; upper 11.5 - (2/5) x 0.5 = 11.3")
case("tie_at_peak", {"frequencies": F7[:4], "psd": [0.0, 8.0, 8.0, 0.0], "drop_db": HALF},
     1, F(1, 2), F(5, 2),
     "two equal peaks: the first, at 1 Hz, is the peak; threshold 4: lower 0.5, and the walk up "
     "passes the second 8 to cross at 2.5")
case("edge_on_a_bin", {"frequencies": F7[:5], "psd": [0.5, 2.0, 20.0, 2.0, 0.5],
                       "drop_db": 10.0}, 2, F(1), F(3),
     "peak 20, 10 dB down is 2, exactly the bins at 1 and 3 Hz, which are the edges")
case("band_hides_a_peak", {"frequencies": F7 + [7.0],
                           "psd": [0.0, 100.0, 0.0, 2.0, 6.0, 8.0, 6.0, 2.0],
                           "drop_db": HALF, "band": [2.5, 7.0]},
     5, crossing(3, 2, 4, 6, 4), crossing(7, 2, 6, 6, 4),
     "band [2.5, 7] keeps bins 3 ... 7, so the 100 at 1 Hz is outside; peak 8 at 5, threshold 4: "
     "3.5 and 6.5")

err("never_falls", {"frequencies": F7[:4], "psd": [1.0, 2.0, 3.0, 2.0], "drop_db": 10.0},
    "10 dB below 3 is 0.3; nothing below the peak on the low side gets there")
err("drop_zero", {"frequencies": F7, "psd": [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0],
                  "drop_db": 0.0}, "drop_db must be positive")
err("drop_negative", {"frequencies": F7, "psd": [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0],
                      "drop_db": -3.0}, "drop_db must be positive")
err("drop_inf", {"frequencies": F7, "psd": [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0],
                 "drop_db": "inf"}, "drop_db must be finite")
err("no_power", {"frequencies": F7[:3], "psd": [0.0, 0.0, 0.0], "drop_db": 3.0},
    "the peak must be positive")
err("band_without_bins", {"frequencies": F7, "psd": [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0],
                          "drop_db": 3.0, "band": [0.2, 0.8]}, "no bin lies in the band")
err("band_reversed", {"frequencies": F7, "psd": [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0],
                      "drop_db": 3.0, "band": [4.0, 1.0]}, "band low must be below band high")

doc = {
    "schema": 1,
    "suite": "db_bandwidth",
    "description": "x dB bandwidth (conventions: Spectra, x dB bandwidth; ADR 0122).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "db_bandwidth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/db_bandwidth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
