"""Writes vectors/cases/spectral_decrease.json in exact fractions, stdlib only.

The decrease weighs each later piece's change in density from the band's first piece by its
width over its distance in bins (conventions: Spectra, Spectral decrease; ADR 0130). The
generator computes it in Fractions and asserts each against a hand value.

Run from the repo root: python vectors/generators/spectral_decrease.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def decrease(freqs, psd, band=None, span=None):
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
            ps.append((b - a, (a + b) / 2, F(p) * delta / (f_r - f_l)))
    _, m0, d0 = ps[0]
    num = sum((d - d0) * w * delta / (m - m0) for w, m, d in ps[1:])
    return num / sum(d * w for w, _, d in ps[1:])


def case(cid, args, want, why):
    got = decrease(args["frequencies"], args["psd"], args.get("band"), args.get("span"))
    assert got == want, (cid, got, want)
    cases.append({"id": f"spectral_decrease.{cid}", "op": "spectral_decrease", "args": args,
                  "expected": float(want), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_decrease.{cid}", "op": "spectral_decrease", "args": args,
                  "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4}, F(0), "flat: every change is 0")
case("falling", {"frequencies": F4, "psd": [4.0, 3.0, 2.0, 1.0]}, F(-1, 2),
     "(-1/1 - 2/2 - 3/3) / (3 + 2 + 1) = -1/2")
case("rising", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0]}, F(1, 3),
     "(1/1 + 2/2 + 3/3) / (2 + 3 + 4) = 1/3")
case("spaced", {"frequencies": [10.0, 30.0, 50.0, 70.0], "psd": [4.0, 3.0, 2.0, 1.0]},
     F(-1, 2), "the falling ramp on 20 Hz bins: distances count in bins, still -1/2")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "band": [0.25, 3.0]},
     (F(8, 5) + F(16, 13) + F(12, 19)) / 7,
     "band [0.25, 3]: piece 0 [1/4, 1/2] at m 3/8, piece 3 [5/2, 3] at m 11/4; terms "
     "1/(5/8), 2/(13/8), (3/2)/(19/8) over power 2 + 3 + 2")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     F(-10, 7), "span (0, 3): bin 0 [0, 1/2] at density 4, m 1/4; bins 1, 2 at 1; bin 3 [5/2, 3] "
     "at 4; terms -3/(3/4), -3/(7/4), 0 over power 1 + 1 + 2")

err("one_piece", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 0.4]},
    "the band holds one bin")
err("no_power_after_first", {"frequencies": F4, "psd": [1.0, 0.0, 0.0, 0.0]},
    "no power after the first bin")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 4.0]},
    "band [0, 4] leaves the spectrum [-0.5, 3.5]")

doc = {
    "schema": 1,
    "suite": "spectral_decrease",
    "description": "Spectral decrease (conventions: Spectra, Spectral decrease; ADR 0130).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_decrease.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_decrease.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
