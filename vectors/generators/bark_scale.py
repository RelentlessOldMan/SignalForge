"""Writes vectors/cases/bark_scale.json, stdlib only.

The Bark scale of Traunmüller (1990) with both corrections (conventions: Bark scale; ADR 0163):
z = 26.81 f/(1960 + f) - 0.53, then z + 0.15 (2 - z) below 2 and z + 0.22 (z - 20.1) above
20.1. Every step is rational, so the values are exact in fractions from the float arguments.

Run from the repo root: python vectors/generators/bark_scale.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-13}
cases = []


def bark(f):
    z = F("26.81") * f / (1960 + f) - F("0.53")
    if z < 2:
        return z + F("0.15") * (2 - z)
    if z > F("20.1"):
        return z + F("0.22") * (z - F("20.1"))
    return z


def hz(b):
    if b < 2:
        z = (b - F("0.3")) / F("0.85")
    elif b > F("20.1"):
        z = (b + F("4.422")) / F("1.22")
    else:
        z = b
    return 1960 * (z + F("0.53")) / (F("26.28") - z)


low_edge = 1960 * F("2.53") / F("24.28")  # z = 2 here
high_edge = 1960 * F("20.63") / F("6.18")  # z = 20.1 here
assert bark(low_edge) == 2 and bark(high_edge) == F("20.1")
assert bark(F(1960)) == F("12.875") and hz(F("12.875")) == 1960
for f in (F(0), F(204), F(205), F(6542), F(6543), F(10**6)):
    assert hz(bark(f)) == f, f


def fwd(cid, f, why):
    cases.append({"id": f"hz_to_bark.{cid}", "op": "hz_to_bark", "args": {"hz": f},
                  "expected": float(bark(F(f))), "tol": TOL, "source": why})


def inv(cid, b, why):
    cases.append({"id": f"bark_to_hz.{cid}", "op": "bark_to_hz", "args": {"bark": b},
                  "expected": float(hz(F(b))), "tol": TOL, "source": why})


fwd("zero", 0.0, "z = -0.53 corrected to -0.53 + 0.15 x 2.53 = -0.1505")
fwd("f_1960", 1960.0, "26.81/2 - 0.53 = 12.875, the middle branch, exact")
fwd("below_2", 204.0, "just below the z = 2 edge (f = 204.23...): low correction, in fractions")
fwd("above_2", 205.0, "just above the z = 2 edge: uncorrected, in fractions")
fwd("below_20_1", 6542.0, "just below the z = 20.1 edge (f = 6542.8...): uncorrected")
fwd("above_20_1", 6543.0, "just above the z = 20.1 edge: high correction, in fractions")
fwd("f_20000", 20000.0, "high correction, in fractions")
fwd("f_1e6", 1e6, "near the limit 27.6396, in fractions")
inv("b_12_875", 12.875, "the middle branch: 1960 (13.405)/(13.405) = 1960 exactly")
inv("zero", 0.0, "low branch: z = -0.3/0.85, then 1960 (z + 0.53)/(26.28 - z), in fractions")
inv("b_1_999", 1.999, "just below 2: low branch, in fractions")
inv("b_2_001", 2.001, "just above 2: middle branch, in fractions")
inv("b_20", 20.0, "just below 20.1: middle branch, in fractions")
inv("b_20_2", 20.2, "just above 20.1: high branch, in fractions")
inv("b_27", 27.0, "near the limit: high branch, in fractions")


def err(op, arg, cid, value, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": {arg: value}, "error": "invalid_argument",
                  "source": why})


err("hz_to_bark", "hz", "negative", -1.0, "hz must be non-negative")
err("hz_to_bark", "hz", "nan", "nan", "hz must be finite")
err("hz_to_bark", "hz", "inf", "inf", "hz must be finite")
err("bark_to_hz", "bark", "below_zero_hz", -0.2, "bark must be at least hz_to_bark(0) = -0.1505")
err("bark_to_hz", "bark", "at_limit", 27.64, "bark must be below the limit 27.6396")
err("bark_to_hz", "bark", "nan", "nan", "bark must be finite")
err("bark_to_hz", "bark", "inf", "inf", "bark must be finite")

doc = {
    "schema": 1,
    "suite": "bark_scale",
    "description": "Bark scale, Traunmüller (1990) with corrections (conventions: Bark scale; ADR 0163).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bark_scale.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bark_scale.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
