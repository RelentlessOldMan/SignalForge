"""Writes vectors/cases/peak_widths.json, stdlib only.

Each case's crossings are worked by hand from the definition (conventions: Spectra, Peak widths;
ADR 0138). The generator holds them as Fractions of a bin and converts them to Hz.

Run from the repo root: python vectors/generators/peak_widths.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, psd, want, why, f0=0, delta=1, **extra):
    """``want`` lists (index, level, left bin, right bin), the bins as Fractions."""
    freqs = [float(f0 + delta * k) for k in range(len(psd))]
    args = {"frequencies": freqs, "psd": psd, **extra}
    expected = []
    for index, level, lo, hi in want:
        left, right = f0 + delta * F(lo), f0 + delta * F(hi)
        expected.append({"index": index, "level": float(level), "left": float(left),
                         "right": float(right), "width": float(right - left)})
    cases.append({"id": f"peak_widths.{cid}", "op": "peak_widths", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"peak_widths.{cid}", "op": "peak_widths", "args": args,
                  "error": "invalid_argument", "source": why})


TRI = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
case("triangle", TRI, [(3, 1.5, F(3, 2), F(9, 2))],
     "height and prominence 3, level 3/2: crossings halfway between bins 1-2 and 4-5")
case("triangle_full", TRI, [(3, 0, 0, 6)],
     "rel_height 1, level 0: the crossings are the zero end bins", rel_height=1.0)
case("triangle_spaced", TRI, [(3, 1.5, F(3, 2), F(9, 2))],
     "the triangle on 10 Hz bins from 100 Hz: 115 Hz to 145 Hz", f0=100, delta=10)
case("triangle_quarter", TRI, [(3, 2.25, F(9, 4), F(15, 4))],
     "rel_height 1/4, level 9/4: a quarter of the way from bin 2 to bin 3, and mirrored",
     rel_height=0.25)
case("asymmetric", [0.0, 2.0, 4.0, 1.0, 0.0], [(2, 2, 1, F(8, 3))],
     "level 2: bin 1 is exactly 2; on the right 4 to 1 crosses 2 at 3 - 1/3")
NESTED = [0.0, 4.0, 1.0, 3.0, 0.5, 0.0]
case("nested", NESTED, [(1, 2, F(1, 2), F(5, 3)), (3, 2, F(5, 2), F(17, 5))],
     "the 4 (prominence 4) has level 2: 0 to 4 crosses at 1/2, 4 to 1 at 2 - 1/3; the 3 "
     "(prominence 2) has level 2: 1 to 3 at 5/2, 3 to 1/2 at 4 - 3/5")
case("threshold", NESTED, [(1, 2, F(1, 2), F(5, 3))],
     "min_prominence 3 keeps only the 4", min_prominence=3.0)
case("plateau", [0.0, 2.0, 2.0, 2.0, 0.0], [(2, 1, F(1, 2), F(7, 2))],
     "the run 1-3 at 2, level 1: crossings halfway out from each end")

T = {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, 1.0, 0.0]}
err("rel_zero", {**T, "rel_height": 0.0}, "rel_height must be > 0")
err("rel_above_one", {**T, "rel_height": 1.5}, "rel_height must be <= 1")
err("rel_nan", {**T, "rel_height": "nan"}, "rel_height must be finite")
err("negative_floor", {**T, "min_prominence": -1.0}, "min_prominence must be >= 0")

doc = {
    "schema": 1,
    "suite": "peak_widths",
    "description": "Peak widths (conventions: Spectra, Peak widths; ADR 0138).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "peak_widths.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/peak_widths.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
