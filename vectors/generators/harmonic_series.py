"""Writes vectors/cases/harmonic_series.json, stdlib only.

Each case's winner, orders and least-squares fundamental are worked by hand from the definition
(conventions: Spectra, Harmonic series; ADR 0139). The fundamental is `Σ m t / Σ m²`, done in
Fractions.

Run from the repo root: python vectors/generators/harmonic_series.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, tones, tolerance, orders, why, max_order=None):
    args = {"frequencies": tones, "tolerance": tolerance}
    if max_order is not None:
        args["max_order"] = max_order
    num = sum(m * F(t) for m, t in zip(orders, tones, strict=True))
    den = sum(m * m for m in orders)
    expected = {"fundamental": float(num / den), "orders": [float(m) for m in orders],
                "matched": float(sum(1 for m in orders if m))}
    cases.append({"id": f"harmonic_series.{cid}", "op": "harmonic_series", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"harmonic_series.{cid}", "op": "harmonic_series", "args": args,
                  "error": "invalid_argument", "source": why})


case("exact", [100.0, 200.0, 300.0, 500.0], 1.0, [1, 2, 3, 5],
     "100 Hz and 50 Hz both match all four; the tie goes to the higher, 100 Hz")
case("detuned", [101.0, 199.0, 302.0], 5.0, [1, 2, 3],
     "101/1, 199/2 and 302/3 all match all three at orders 1, 2, 3, as do their halves; "
     "fundamental (101 + 398 + 906)/14 = 1405/14")
case("stray", [100.0, 200.0, 250.0, 300.0], 2.0, [2, 4, 5, 6],
     "the 250 Hz tone makes 50 Hz match all four, so it beats 100 Hz's three")
case("stray_low_order", [100.0, 200.0, 250.0, 300.0], 2.0, [1, 2, 0, 3],
     "with max_order 4, 50 Hz matches only 100 and 200; 100 Hz matches three, 250 unmatched",
     max_order=4)
case("missing_fundamental", [300.0, 200.0, 400.0], 0.5, [3, 2, 4],
     "200, 300 and 400 Hz in any order: 100 Hz matches all three, and is the highest that does")
case("single", [440.0], 1.0, [1], "one tone is its own fundamental, the highest candidate")

err("no_tones", {"frequencies": [], "tolerance": 1.0}, "need at least one tone")
err("negative_tone", {"frequencies": [100.0, -200.0], "tolerance": 1.0},
    "tones must be positive")
err("zero_tolerance", {"frequencies": [100.0], "tolerance": 0.0}, "tolerance must be > 0")
err("max_order_zero", {"frequencies": [100.0], "tolerance": 1.0, "max_order": 0},
    "max_order must be at least 1")

doc = {
    "schema": 1,
    "suite": "harmonic_series",
    "description": "Harmonic series (conventions: Spectra, Harmonic series; ADR 0139).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "harmonic_series.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/harmonic_series.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
