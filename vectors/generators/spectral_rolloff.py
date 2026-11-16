"""Writes vectors/cases/spectral_rolloff.json in exact fractions, stdlib only.

The PSD is a step density, constant over each bin (conventions: Spectra, Spectral rolloff; ADR
0124). The generator walks the bins with Fractions to the point where the running power reaches
the fraction. Every case also states the hand-worked answer, and the generator asserts that the
walk agrees with it. A fraction is read as the decimal it is written as (0.85 is 17/20), so the
hand values are exact; the libraries' doubles differ from that by far less than TOL.

Run from the repo root: python vectors/generators/spectral_rolloff.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def rolloff(freqs, psd, fraction, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    pieces = []
    for f_l, f_r, p in zip(left, right, psd):
        a, b = max(f_l, lo), min(f_r, hi)
        if b > a:
            pieces.append((a, b, F(p) * delta / (f_r - f_l)))
    target = F(str(fraction)) * sum(d * (b - a) for a, b, d in pieces)
    running = F(0)
    for a, b, d in pieces:
        if running + d * (b - a) >= target:
            return a + (target - running) / d
        running += d * (b - a)
    raise AssertionError("unreachable in exact arithmetic")


def case(cid, args, want, why):
    got = rolloff(args["frequencies"], args["psd"], args["fraction"], args.get("band"),
                  args.get("span"))
    assert got == want, (cid, got, want)
    cases.append({"id": f"spectral_rolloff.{cid}", "op": "spectral_rolloff", "args": args,
                  "expected": float(want), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_rolloff.{cid}", "op": "spectral_rolloff", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
FLAT = [1.0] * 4
case("flat_85", {"frequencies": F4, "psd": FLAT, "fraction": 0.85}, F(29, 10),
     "flat over [-0.5, 3.5]: rolloff = -0.5 + 0.85 x 4 = 2.9")
case("flat_half", {"frequencies": F4, "psd": FLAT, "fraction": 0.5}, F(3, 2),
     "flat over [-0.5, 3.5]: half the power lies below the centre, 1.5")
case("flat_all", {"frequencies": F4, "psd": FLAT, "fraction": 1.0}, F(7, 2),
     "fraction 1 on a flat PSD: the top edge, 3.5")
case("uneven", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "fraction": 0.5}, F(13, 6),
     "power 10, target 5: bins 0 and 1 hold 3, so 2 more of bin 2's density 3, at 1.5 + 2/3")
case("empty_before", {"frequencies": F4, "psd": [0.0, 0.0, 2.0, 2.0], "fraction": 0.25},
     F(2),
     "power 4, target 1: bins 0 and 1 are empty, so 1/2 Hz into bin 2 (density 2), at 1.5 + 0.5")
case("tie_empty_after", {"frequencies": F4, "psd": [1.0, 1.0, 0.0, 2.0], "fraction": 0.5},
     F(3, 2),
     "power 4, target 2: reached exactly at the top of bin 1, before the empty bin 2: 1.5")
case("all_stops_at_last_power", {"frequencies": F4, "psd": [1.0, 1.0, 0.0, 0.0],
                                 "fraction": 1.0}, F(3, 2),
     "fraction 1: the top edge of the last bin with power, 1.5, not the spectrum's 3.5")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "band": [0.0, 2.0],
                  "fraction": 0.5}, F(5, 4),
     "band [0, 2]: pieces [0, 0.5] at density 1, [0.5, 1.5] at 2, [1.5, 2] at 3; power 4, "
     "target 2: 0.5 before bin 1, 1.5 more at density 2 is 0.75 Hz, at 0.5 + 0.75 = 1.25")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0],
                      "fraction": 0.25}, F(3, 8),
     "span (0, 3) halves bin 0, which keeps power 2 at density 4; power 6, target 1.5, "
     "reached 1.5 / 4 into [0, 0.5]: 0.375")
case("offset_axis", {"frequencies": [1000.0, 1001.0, 1002.0], "psd": [1.0, 4.0, 1.0],
                     "fraction": 0.95}, F(5011, 5),
     "power 6, target 5.7: bins 0 and 1 hold 5, then 0.7 of bin 2 (density 1): 1001.5 + 0.7 "
     "= 1002.2")

err("fraction_zero", {"frequencies": F4, "psd": FLAT, "fraction": 0.0},
    "fraction must be in (0, 1]")
err("fraction_above_one", {"frequencies": F4, "psd": FLAT, "fraction": 1.5},
    "fraction must be in (0, 1]")
err("fraction_nan", {"frequencies": F4, "psd": FLAT, "fraction": "nan"},
    "fraction must be finite")
err("band_reversed", {"frequencies": F4, "psd": FLAT, "fraction": 0.5, "band": [2.0, 1.0]},
    "band low must be below band high")
err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "fraction": 0.5,
                 "band": [-0.5, 1.5]}, "the band has no power")

doc = {
    "schema": 1,
    "suite": "spectral_rolloff",
    "description": "Spectral rolloff (conventions: Spectra, Spectral rolloff; ADR 0124).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_rolloff.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_rolloff.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
