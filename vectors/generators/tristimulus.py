"""Writes vectors/cases/tristimulus.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Spectra,
Tristimulus; ADR 0142). The heights are perfect squares, so the amplitudes `sqrt(h)` are exact.

Run from the repo root: python vectors/generators/tristimulus.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, amplitudes, orders, why):
    heights = [float(a * a) for a in amplitudes]
    bands = [F(0)] * 3
    for a, m in zip(amplitudes, orders, strict=True):
        if m == 1:
            bands[0] += a
        elif 2 <= m <= 4:
            bands[1] += a
        elif m >= 5:
            bands[2] += a
    total = sum(bands)
    first, second, third = (float(b / total) for b in bands)
    cases.append({"id": f"tristimulus.{cid}", "op": "tristimulus",
                  "args": {"heights": heights, "orders": orders},
                  "expected": {"first": first, "second": second, "third": third},
                  "tol": TOL, "source": why})


def err(cid, heights, orders, why):
    cases.append({"id": f"tristimulus.{cid}", "op": "tristimulus",
                  "args": {"heights": heights, "orders": orders},
                  "error": "invalid_argument", "source": why})


case("all_bands", [4, 2, 1, 1, 2, 3], [1, 2, 3, 4, 5, 6],
     "amplitudes 4 | 2 + 1 + 1 | 2 + 3 of 13: 4/13, 4/13, 5/13")
case("fundamental_only", [3], [1], "all of it in the fundamental: 1, 0, 0")
case("missing_fundamental", [2, 1], [2, 7], "amplitudes 2 | 1 of 3: 0, 2/3, 1/3")
case("unmatched", [5, 10, 3], [1, 0, 3], "order 0 left out: amplitudes 5 | 3 of 8: 5/8, 3/8, 0")

err("nothing", [1.0, 4.0], [0, 0], "no harmonic tones")
err("all_silent", [0.0, 0.0], [1, 2], "the harmonics have no power")
err("length_mismatch", [1.0, 4.0], [1], "orders is shorter than heights")
err("negative_height", [1.0, -4.0], [1, 2], "heights must be non-negative")
err("negative_order", [1.0, 4.0], [1, -2], "orders must be >= 0")

doc = {
    "schema": 1,
    "suite": "tristimulus",
    "description": "Tristimulus (conventions: Spectra, Tristimulus; ADR 0142).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tristimulus.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tristimulus.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
