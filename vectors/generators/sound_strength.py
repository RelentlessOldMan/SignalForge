"""Writes vectors/cases/sound_strength.json, stdlib only.

Sound strength (conventions: Sound strength; ADR 0178): G = 10 log10(sum |h|^2 / sum |h_ref|^2),
as exact hand sums in fractions with the logarithm in 50-digit decimal.

Run from the repo root: python vectors/generators/sound_strength.py [--check]
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
    ratio = F(ratio)
    return float(10 * (D(ratio.numerator) / D(ratio.denominator)).log10())


def add(cid, ir, ref, expected, why):
    cases.append({"id": f"sound_strength.{cid}", "op": "sound_strength",
                  "args": {"impulse_response": ir, "reference": ref},
                  "expected": expected, "tol": TOL, "source": why})


REF = [0.0, 0.5, 0.25]
add("itself", REF, REF, 0.0, "the reference against itself: 0 dB")
add("doubled", [0.0, 1.0, 0.5], REF, db(4), "twice the amplitude: 10 log10 4 = 20 log10 2")
add("unequal_lengths", [1.0, 0.5, 0.5, 0.25, 0.25, 0.25], REF, db(F(27, 5)),
    "6 samples against 3: 1 + 1/4 + 1/4 + 3/16 = 27/16 against 1/4 + 1/16 = 5/16, ratio 27/5")
add("room", [1.0, 0.8, 0.6, 0.4, 0.2], [0.3], db(F(22, 10) / F(9, 100)),
    "1 + 0.64 + 0.36 + 0.16 + 0.04 = 2.2 against 0.09: 10 log10(220/9)")
add("complex", {"re": [3.0, 0.0], "im": [4.0, 1.0]}, {"re": [1.0], "im": [0.0]}, db(26),
    "|h|^2 = 25 + 1 against 1: 10 log10 26")
add("silent", [0.0, 0.0], REF, "-inf", "no energy: -inf")


def err(cid, change, why):
    args = {"impulse_response": [1.0, 0.5], "reference": [0.5]}
    args.update(change)
    cases.append({"id": f"sound_strength.{cid}", "op": "sound_strength", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"impulse_response": []}, "impulse_response must not be empty")
err("empty_reference", {"reference": []}, "reference must not be empty")
err("silent_reference", {"reference": [0.0, 0.0]}, "reference must not be all zero")
err("nan", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("inf_reference", {"reference": ["inf"]}, "reference must be finite")

doc = {
    "schema": 1,
    "suite": "sound_strength",
    "description": "Sound strength (conventions: Sound strength; ADR 0178).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sound_strength.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sound_strength.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
