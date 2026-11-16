"""Writes vectors/cases/odd_even_ratio.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Spectra,
Odd-to-even ratio; ADR 0141): `Σ h` over odd orders over `Σ h` over even orders, order 0 left
out, the fundamental counted as odd.

Run from the repo root: python vectors/generators/odd_even_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, heights, orders, want, why):
    expected = "inf" if want == "inf" else float(want)
    cases.append({"id": f"odd_even_ratio.{cid}", "op": "odd_even_ratio",
                  "args": {"heights": heights, "orders": orders},
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, heights, orders, why):
    cases.append({"id": f"odd_even_ratio.{cid}", "op": "odd_even_ratio",
                  "args": {"heights": heights, "orders": orders},
                  "error": "invalid_argument", "source": why})


case("mixed", [4.0, 1.0, 2.0, 1.0], [1, 2, 3, 4], 3, "odd 4 + 2 = 6 over even 1 + 1 = 2")
case("any_sequence", [1.0, 2.0, 3.0], [2, 1, 3], 5, "odd 2 + 3 = 5 over even 1")
case("unmatched", [1.0, 9.0, 3.0], [1, 0, 2], F(1, 3), "order 0 left out: odd 1 over even 3")
case("odd_only", [1.0, 0.25, 0.0625], [1, 3, 5], "inf",
     "a square wave's odd harmonics only: no even power gives inf")
case("even_only", [1.0, 2.0], [2, 4], 0, "no odd power over even 3")
case("silent_even", [2.0, 0.0], [1, 2], "inf", "the even tone has no power")

err("nothing", [1.0, 2.0], [0, 0], "no harmonic tones")
err("all_silent", [0.0, 0.0], [1, 2], "the harmonics have no power")
err("length_mismatch", [1.0, 2.0], [1], "orders is shorter than heights")
err("negative_height", [1.0, -2.0], [1, 2], "heights must be non-negative")
err("negative_order", [1.0, 2.0], [1, -2], "orders must be >= 0")

doc = {
    "schema": 1,
    "suite": "odd_even_ratio",
    "description": "Odd-to-even harmonic ratio (conventions: Spectra, Odd-to-even ratio; ADR 0141).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "odd_even_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/odd_even_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
