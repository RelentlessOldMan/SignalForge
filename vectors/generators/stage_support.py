"""Writes vectors/cases/stage_support.json, stdlib only.

Stage support (conventions: Stage support; ADR 0179): windows [0, N(0.01)), [N(0.02), N(0.1)),
[N(0.1), N(1)), N(t) = floor(t fs + 1/2), clipped to the length; 10 log10(E_window/E_direct) as
exact hand sums in fractions and geometric window sums (q^a - q^b)/(1 - q) in 50-digit decimal.

Run from the repo root: python vectors/generators/stage_support.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as F

getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []


def db(ratio):
    if isinstance(ratio, F):
        ratio = D(ratio.numerator) / D(ratio.denominator)
    return float(10 * ratio.log10())


def add(cid, ir, fs, expected, why, late=None):
    args = {"impulse_response": ir, "sample_rate": fs}
    if late is not None:
        args["late"] = late
    cases.append({"id": f"stage_support.{cid}", "op": "stage_support", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def window(r, a, b):
    q = D(r) ** 2
    return (q ** a - q ** b) / (1 - q)


GEO = [0.99 ** n for n in range(1500)]
add("geometric_early", GEO, 1000.0, db(window("0.99", 20, 100) / window("0.99", 0, 10)),
    "h = 0.99^n at 1 kHz: S(20, 100)/S(0, 10), q = 0.9801")
add("geometric_late", GEO, 1000.0, db(window("0.99", 100, 1000) / window("0.99", 0, 10)),
    "the same decay: S(100, 1000)/S(0, 10)", late=True)
HAND = [2.0, 9.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
add("hand_early", HAND, 100.0, db(F(2, 4)),
    "100 Hz: direct [0, 1) = 4, early [2, 10) = 1 + 1 = 2 (sample 1 is in neither): 10 log10(1/2)")
add("hand_late", HAND, 100.0, db(F(2, 4)),
    "late [10, 100) clipped to [10, 12) = 2 against 4", late=True)
add("complex", {"re": [3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "im": [4.0, 0.0, 5.0, 0.0, 0.0, 0.0,
                                                                   0.0]},
    100.0, 0.0, "direct |3 + 4j|^2 = 25, early sample 2: 25, 0 dB")
add("silent_late", [1.0, 0.0, 1.0], 100.0, "-inf", "late window [10, 100) is past the end: -inf",
    late=True)


def err(cid, change, why):
    args = {"impulse_response": [1.0, 0.5, 0.25], "sample_rate": 100.0}
    args.update(change)
    cases.append({"id": f"stage_support.{cid}", "op": "stage_support", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"impulse_response": []}, "impulse_response must not be empty")
err("silent_direct", {"impulse_response": [0.0, 1.0, 1.0]}, "the direct window has no energy")
err("nan", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("low_rate", {"sample_rate": 40.0}, "40 Hz: N(0.01) = floor(0.9) = 0 direct samples")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")

doc = {
    "schema": 1,
    "suite": "stage_support",
    "description": "Stage support (conventions: Stage support; ADR 0179).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "stage_support.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/stage_support.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
