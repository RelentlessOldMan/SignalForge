"""Writes vectors/cases/harmonic_deviation.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Spectra, Harmonic
deviation; ADR 0144). The heights are chosen so each order's summed power is a perfect square,
so the amplitudes are exact. The generator checks the hand value against the definition.

Run from the repo root: python vectors/generators/harmonic_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def definition(heights, orders):
    top = max(orders)
    power = [0] * (top + 1)
    for h, m in zip(heights, orders, strict=True):
        power[m] += h
    a = []
    for p in power[1:]:
        r = math.isqrt(p)
        assert r * r == p, p
        a.append(F(r))
    spread = F(0)
    for k in range(top):
        near = a[max(k - 1, 0) : min(k + 1, top - 1) + 1]
        spread += abs(a[k] - sum(near) / len(near))
    return spread / sum(a)


def case(cid, heights, orders, want, why):
    assert definition(heights, orders) == want, (cid, definition(heights, orders), want)
    cases.append({"id": f"harmonic_deviation.{cid}", "op": "harmonic_deviation",
                  "args": {"heights": [float(h) for h in heights], "orders": orders},
                  "expected": float(want), "tol": TOL, "source": why})


def err(cid, heights, orders, why):
    cases.append({"id": f"harmonic_deviation.{cid}", "op": "harmonic_deviation",
                  "args": {"heights": heights, "orders": orders},
                  "error": "invalid_argument", "source": why})


case("flat", [1, 1, 1, 1], [1, 2, 3, 4], F(0), "equal amplitudes match their envelope")
case("bowl", [36, 9, 9, 36], [1, 2, 3, 4], F(5, 18),
     "amplitudes 6, 3, 3, 6; envelope 9/2, 4, 4, 9/2; |deviations| 3/2 + 1 + 1 + 3/2 = 5 over 18")
case("gap", [16, 4], [1, 3], F(5, 6),
     "amplitudes 4, 0, 2 (order 2 missing); envelope 2, 2, 1; 2 + 2 + 1 = 5 over 6")
case("duplicates", [9, 16, 1], [1, 1, 2], F(2, 3),
     "order 1 powers 9 + 16 = 25, amplitude 5; order 2 amplitude 1; envelope 3, 3; 4 over 6")
case("unmatched", [4, 100, 1], [1, 0, 2], F(1, 3),
     "order 0 left out: amplitudes 2, 1; envelope 3/2, 3/2; 1 over 3")
case("permuted", [36, 9, 9, 36], [4, 2, 3, 1], F(5, 18), "the bowl, tones in another order")
case("single", [4], [1], F(0), "one harmonic is its own envelope")

err("nothing", [1.0, 4.0], [0, 0], "no tone has order >= 1")
err("all_silent", [0.0, 0.0], [1, 2], "the harmonics have no power")
err("length_mismatch", [1.0, 4.0], [1], "orders is shorter than heights")
err("negative_height", [1.0, -4.0], [1, 2], "heights must be non-negative")
err("negative_order", [1.0, 4.0], [1, -2], "orders must be >= 0")

doc = {
    "schema": 1,
    "suite": "harmonic_deviation",
    "description": "Harmonic spectral deviation (conventions: Spectra, Harmonic deviation; "
    "ADR 0144).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "harmonic_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/harmonic_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
