"""Writes vectors/cases/spectral_irregularity.json in exact fractions, stdlib only.

The irregularity is the squared jumps between neighbouring pieces of the step density, each
weighted by the two pieces' mean width, over the density's squared norm (conventions: Spectra,
Spectral irregularity; ADR 0132). The generator computes it in Fractions and asserts each against
a hand value.

Run from the repo root: python vectors/generators/spectral_irregularity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def irregularity(freqs, psd, band=None, span=None):
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
    jumps = sum((d1 - d0) ** 2 * (w0 + w1) / 2 for (w0, d0), (w1, d1) in zip(ps, ps[1:]))
    return jumps / sum(d * d * w for w, d in ps)


def case(cid, args, want, why):
    got = irregularity(args["frequencies"], args["psd"], args.get("band"), args.get("span"))
    assert got == want, (cid, got, want)
    cases.append({"id": f"spectral_irregularity.{cid}", "op": "spectral_irregularity",
                  "args": args, "expected": float(want), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_irregularity.{cid}", "op": "spectral_irregularity",
                  "args": args, "error": "invalid_argument", "source": why})


F4 = [0.0, 1.0, 2.0, 3.0]
case("flat", {"frequencies": F4, "psd": [2.0] * 4}, F(0), "flat: no jumps")
case("ramp", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0]}, F(1, 10),
     "three unit jumps over 1 + 4 + 9 + 16 = 30")
case("alternating", {"frequencies": F4, "psd": [1.0, 0.0, 1.0, 0.0]}, F(3, 2),
     "three unit jumps over 1 + 1 = 2")
case("single_bin", {"frequencies": F4, "psd": [0.0, 1.0, 0.0, 0.0]}, F(2),
     "two unit jumps over 1")
case("spaced", {"frequencies": [10.0, 30.0, 50.0, 70.0], "psd": [1.0, 2.0, 3.0, 4.0]},
     F(1, 10), "the ramp on 20 Hz bins: still 1/10")
case("cut_band", {"frequencies": F4, "psd": [1.0, 2.0, 3.0, 4.0], "band": [0.25, 3.0]},
     F(19, 170), "band [0.25, 3], widths 1/4, 1, 1, 1/2: jumps 5/8 + 1 + 3/4 = 19/8 over "
     "1/4 + 4 + 9 + 8 = 85/4")
case("span_clipped", {"frequencies": F4, "psd": [2.0, 1.0, 1.0, 2.0], "span": [0.0, 3.0]},
     F(3, 4), "span (0, 3): densities 4, 1, 1, 4 on widths 1/2, 1, 1, 1/2; jumps 9 x 3/4 twice "
     "= 27/2 over 8 + 1 + 1 + 8 = 18")

err("one_piece", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 0.4]},
    "the band holds one bin")
err("no_power", {"frequencies": F4, "psd": [0.0] * 4}, "the band has no power")
err("band_outside", {"frequencies": F4, "psd": [1.0] * 4, "band": [0.0, 4.0]},
    "band [0, 4] leaves the spectrum [-0.5, 3.5]")

doc = {
    "schema": 1,
    "suite": "spectral_irregularity",
    "description": "Spectral irregularity (conventions: Spectra, Spectral irregularity; "
    "ADR 0132).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_irregularity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_irregularity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
