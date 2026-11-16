"""Writes vectors/cases/spectral_entropy.json, stdlib only.

The entropy is the differential entropy of the band's step density normalized to unit power
(conventions: Spectra, Spectral entropy; ADR 0128). Shares and densities are exact Fractions,
and the logs are taken once each. The generator uses entropy = ln power - sum q_k ln d_k, a
different algebra from the libraries'. Hand-known entropy bandwidths are asserted exactly in
Fractions before any log: a flat band's W, a single bin's width, and two equal bins' 2.

Run from the repo root: python vectors/generators/spectral_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def pieces(freqs, psd, band=None, span=None):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    out = []
    for f_l, f_r, p in zip(left, right, psd):
        a, b = max(f_l, lo), min(f_r, hi)
        if b > a:
            out.append((b - a, F(p) * delta / (f_r - f_l)))
    return out, hi - lo


def case(cid, args, why, flat_width=None):
    ps, width = pieces(args["frequencies"], args["psd"], args.get("band"), args.get("span"))
    power = sum(w * d for w, d in ps)
    live = [(w * d / power, d) for w, d in ps if d > 0]
    if flat_width is not None:
        # Flat over a total width t: every live density is power / t, so the bandwidth is t.
        assert all(d == power / flat_width for _, d in live), cid
    h = math.log(power) - sum(float(q) * math.log(d) for q, d in live)
    bw = math.exp(h)
    if flat_width is not None:
        bw = float(flat_width)
        h = math.log(flat_width)
    cases.append({"id": f"spectral_entropy.{cid}", "op": "spectral_entropy", "args": args,
                  "expected": {"entropy": h, "entropy_bandwidth": bw,
                               "normalized": bw / float(width)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_entropy.{cid}", "op": "spectral_entropy", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4},
     "flat over a width of 4: entropy ln 4, bandwidth 4, normalized 1", F(4))
case("single_bin", {"frequencies": F4, "psd": [0.0, 5.0, 0.0, 0.0]},
     "all power flat in one bin of width 1: entropy 0, bandwidth 1, normalized 1/4", F(1))
case("two_ends", {"frequencies": F4, "psd": [1.0, 0.0, 0.0, 1.0]},
     "two equal bins of width 1: entropy ln 2, bandwidth 2, normalized 1/2", F(2))
case("narrow_bins", {"frequencies": [0.0, 0.25, 0.5, 0.75], "psd": [0.0, 1.0, 0.0, 0.0]},
     "one bin of width 1/4: entropy ln(1/4) < 0, bandwidth 1/4, normalized 1/4", F(1, 4))
case("uneven", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0]},
     "shares 0.1, 0.2, 0.3, 0.4 on unit bins: entropy -sum q ln q")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "band": [0.25, 2.75]},
     "band [0.25, 2.75] cuts bins 0 and 3 to a quarter")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     "span (0, 3): halved bins 0 and 3 at density 4, inner bins at 1; power 6")

err("no_power", {"frequencies": F4, "psd": [0.0, 0.0, 1.0, 0.0], "band": [-0.5, 1.5]},
    "the band has no power")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [-1.0, 3.0]},
    "band [-1, 3] leaves the spectrum [-0.5, 3.5]")
err("one_bin", {"frequencies": [0.0], "psd": [1.0]}, "need at least two bins")

doc = {
    "schema": 1,
    "suite": "spectral_entropy",
    "description": "Spectral entropy (conventions: Spectra, Spectral entropy; ADR 0128).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
