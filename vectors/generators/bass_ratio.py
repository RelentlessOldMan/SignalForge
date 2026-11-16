"""Writes vectors/cases/bass_ratio.json, stdlib only.

Bass and treble ratio (conventions: Bass and treble ratio; ADR 0180): from the six octave-band
times at 125 Hz to 4 kHz, BR = (T125 + T250)/(T500 + T1000) and TR = (T2000 + T4000)/(T500 +
T1000), as exact fractions.

Run from the repo root: python vectors/generators/bass_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(op, cid, times, expected, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": {"times": times},
                  "expected": float(expected), "tol": TOL, "source": why})


HALL = [2.5, 2.25, 2.0, 2.0, 1.75, 1.5]
add("bass_ratio", "hall", HALL, F(475, 400), "(2.5 + 2.25)/(2 + 2) = 4.75/4 = 19/16")
add("treble_ratio", "hall", HALL, F(325, 400), "(1.75 + 1.5)/(2 + 2) = 3.25/4 = 13/16")
FLAT = [1.2] * 6
add("bass_ratio", "flat", FLAT, 1, "equal times: 1")
add("treble_ratio", "flat", FLAT, 1, "equal times: 1")
DRY = [0.5, 0.75, 1.0, 1.5, 1.25, 1.25]
add("bass_ratio", "rising", DRY, F(125, 250), "(0.5 + 0.75)/(1 + 1.5) = 1.25/2.5 = 1/2")
add("treble_ratio", "rising", DRY, 1, "(1.25 + 1.25)/(1 + 1.5) = 1")


def err(op, cid, times, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": {"times": times},
                  "error": "invalid_argument", "source": why})


for op in ("bass_ratio", "treble_ratio"):
    err(op, "five", [1.0] * 5, "five times: exactly six are required")
    err(op, "seven", [1.0] * 7, "seven times: exactly six are required")
    err(op, "zero", [1.0, 1.0, 1.0, 0.0, 1.0, 1.0], "a zero time")
    err(op, "negative_unused", [1.0, 1.0, 1.0, 1.0, 1.0, -1.0] if op == "bass_ratio"
        else [-1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "a negative time in a band the ratio doesn't use")
    err(op, "nan", [1.0, "nan", 1.0, 1.0, 1.0, 1.0], "a NaN time")
    err(op, "inf", [1.0, 1.0, "inf", 1.0, 1.0, 1.0], "an infinite time")

doc = {
    "schema": 1,
    "suite": "bass_ratio",
    "description": "Bass and treble ratio (conventions: Bass and treble ratio; ADR 0180).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bass_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bass_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
