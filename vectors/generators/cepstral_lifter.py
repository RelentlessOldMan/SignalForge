"""Writes vectors/cases/cepstral_lifter.json, stdlib only.

HTK sinusoidal lifter (conventions: Cepstral liftering; ADR 0159): c'_n = (1 + (L/2) sin(pi n /
L)) c_n, with sin(pi n / L) exact. For L = 12 the sines of multiples of 15 degrees are
(sqrt(6) - sqrt(2))/4, 1/2, sqrt(2)/2, sqrt(3)/2, (sqrt(6) + sqrt(2))/4 and 1, and their
reflections; for L = 1, 2 and 22 only 0 and +-1 are needed. All in 50-digit decimal.

Run from the repo root: python vectors/generators/cepstral_lifter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []
R2, R3, R6 = D(2).sqrt(), D(3).sqrt(), D(6).sqrt()
UP = [D(0), (R6 - R2) / 4, D(1) / 2, R2 / 2, R3 / 2, (R6 + R2) / 4, D(1)]  # 0 .. 90 degrees
HALF = UP + list(reversed(UP[:-1]))[:-1]  # 0 .. 165 degrees, 12 values
SIN12 = HALF + [-v for v in HALF]  # sin(k pi / 12), k = 0 .. 23


def sine(n, length):
    """sin(pi n / L), exact, or None when it is not a multiple of 15 degrees here."""
    if length == 12:
        return SIN12[n % 24]
    if (2 * n) % length:
        return None
    return [D(0), D(1), D(0), D(-1)][(2 * n // length) % 4]  # a multiple of pi/2


def case(cid, coefficients, length, why):
    out = []
    for n, c in enumerate(coefficients):
        if c == 0:
            out.append(D(0))  # any weight times 0
            continue
        s = sine(n, length)
        assert s is not None, (cid, n)
        out.append((1 + D(length) / 2 * s) * D(c))
    args = {"coefficients": coefficients}
    if length != 22:
        args["length"] = length
    cases.append({"id": f"cepstral_lifter.{cid}", "op": "cepstral_lifter", "args": args,
                  "expected": [float(v) for v in out], "tol": TOL, "source": why})


assert SIN12[6] == 1 and SIN12[12] == 0 and SIN12[18] == -1 and len(SIN12) == 24
case("length12", [1.0] * 15, 12,
     "L = 12 on ones, n = 0..14: weights 1 + 6 sin(n pi/12), exact sines of 15-degree steps; "
     "n = 13, 14 are below 1")
case("length12_values", [2.0, -1.0, 0.5, 3.0, -4.0, 0.25, 1.5], 12,
     "L = 12 times mixed coefficients: weights 1, 1 + 6 (sqrt 6 - sqrt 2)/4, 4, 1 + 3 sqrt 2, "
     "1 + 3 sqrt 3, ..., 7")
case("length2", [1.0, 1.0, 1.0, 1.0, 1.0], 2, "L = 2: sin(pi n/2) = 0, 1, 0, -1, 0, so weights "
     "1, 2, 1, 0, 1")
case("length1", [3.0, -2.0, 5.0], 1, "L = 1: sin(pi n) = 0, every weight is 1")
case("default", [0.0] * 11 + [1.0], 22, "default L = 22: at n = 11, sin(pi/2) = 1, weight 12")


def err(cid, args, why):
    cases.append({"id": f"cepstral_lifter.{cid}", "op": "cepstral_lifter", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"coefficients": []}, "needs at least one value")
err("nan", {"coefficients": [1.0, "nan"]}, "values must be finite")
err("zero_length", {"coefficients": [1.0], "length": 0}, "length must be at least 1")
err("negative_length", {"coefficients": [1.0], "length": -3}, "length must be at least 1")

doc = {
    "schema": 1,
    "suite": "cepstral_lifter",
    "description": "HTK sinusoidal cepstral lifter (conventions: Cepstral liftering; ADR 0159).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cepstral_lifter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cepstral_lifter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
