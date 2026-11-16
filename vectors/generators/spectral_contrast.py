"""Writes vectors/cases/spectral_contrast.json, stdlib only.

The peak and valley are the mean step densities over the top and bottom fraction of the band's
width after sorting the pieces by density (conventions: Spectra, Spectral contrast; ADR 0133).
The generator computes both in exact Fractions and asserts each against a hand value. Only the
dB is taken in floating point.

Run from the repo root: python vectors/generators/spectral_contrast.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def fill(ps, width):
    taken = acc = F(0)
    for w, d in ps:
        t = min(w, width - taken)
        if t <= 0:
            break
        acc += t * d
        taken += t
    return acc / width


def contrast(freqs, psd, band=None, span=None, fraction=0.2):
    delta = F(freqs[1]) - F(freqs[0])
    left = [F(f) - delta / 2 for f in freqs]
    right = [F(f) + delta / 2 for f in freqs]
    if span is not None:
        left = [max(x, F(span[0])) for x in left]
        right = [min(x, F(span[1])) for x in right]
    lo, hi = (left[0], right[-1]) if band is None else (F(band[0]), F(band[1]))
    ps = []
    for f_l, f_r, p in zip(left, right, psd):
        a, b = max(f_l, lo), min(f_r, hi)
        if b > a:
            ps.append((b - a, F(p) * delta / (f_r - f_l)))
    width = F(str(fraction)) * sum(w for w, _ in ps)
    up = sorted(ps, key=lambda p: p[1])
    return fill(up[::-1], width), fill(up, width)


def case(cid, args, peak, valley, why):
    got = contrast(args["frequencies"], args["psd"], args.get("band"), args.get("span"),
                   args.get("fraction", 0.2))
    assert got == (peak, valley), (cid, got, peak, valley)
    cases.append({"id": f"spectral_contrast.{cid}", "op": "spectral_contrast", "args": args,
                  "expected": {"peak": float(peak), "valley": float(valley),
                               "contrast_db": 10 * math.log10(peak / valley)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_contrast.{cid}", "op": "spectral_contrast", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
RAMP = [1.0, 2.0, 3.0, 4.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4}, F(2), F(2), "flat: peak = valley, 0 dB")
case("ramp_default", {"frequencies": F4, "psd": RAMP}, F(4), F(1),
     "fraction 0.2 of width 4 is 0.8, inside the top and bottom bins: peak 4, valley 1")
case("ramp_quarter", {"frequencies": F4, "psd": RAMP, "fraction": 0.25}, F(4), F(1),
     "fraction 1/4: exactly the top and bottom bins")
case("ramp_half", {"frequencies": F4, "psd": RAMP, "fraction": 0.5}, F(7, 2), F(3, 2),
     "fraction 1/2: (4 + 3)/2 and (1 + 2)/2")
case("ramp_split", {"frequencies": F4, "psd": RAMP, "fraction": 0.375}, F(11, 3), F(4, 3),
     "fraction 3/8, width 3/2: (4 + 3/2)/(3/2) and (1 + 1)/(3/2), splitting the second bins")
case("unsorted", {"frequencies": F4, "psd": [3.0, 1.0, 4.0, 2.0], "fraction": 0.5},
     F(7, 2), F(3, 2), "the ramp shuffled: sorting gives the same as ramp_half")
case("cut_band", {"frequencies": F4, "psd": RAMP, "band": [0.25, 3.0], "fraction": 0.25},
     F(41, 11), F(18, 11),
     "band [0.25, 3], widths 1/4, 1, 1, 1/2, W 11/4, limit 11/16: top 4 x 1/2 + 3 x 3/16, bottom "
     "1 x 1/4 + 2 x 7/16, each over 11/16")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0],
                      "fraction": 0.5}, F(3), F(1),
     "span (0, 3): densities 4, 1, 1, 4 on widths 1/2, 1, 1, 1/2; half of 3 is 3/2: top "
     "4 x 1/2 + 4 x 1/2 + 1 x 1/2 over 3/2, bottom 1 + 1 x 1/2 over 3/2")

err("fraction_zero", {"frequencies": F4, "psd": RAMP, "fraction": 0.0}, "fraction must be > 0")
err("fraction_over_half", {"frequencies": F4, "psd": RAMP, "fraction": 0.6},
    "fraction must be at most 1/2")
err("no_power", {"frequencies": F4, "psd": [0.0] * 4}, "the band has no power")
err("band_outside", {"frequencies": F4, "psd": RAMP, "band": [0.0, 4.0]},
    "band [0, 4] leaves the spectrum [-0.5, 3.5]")

doc = {
    "schema": 1,
    "suite": "spectral_contrast",
    "description": "Spectral contrast (conventions: Spectra, Spectral contrast; ADR 0133).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_contrast.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_contrast.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
