"""Writes vectors/cases/erb_scale.json, stdlib only.

ERB scale after Glasberg & Moore (1990) with the published constants (conventions: ERB scale;
ADR 0160): ERB(f) = 24.7 (4.37 f/1000 + 1), E(f) = 21.4 log10(4.37 f/1000 + 1) and its
inverse, in 50-digit decimal from the float arguments. The generator checks that
f = (1000/4.37)(10^k - 1) gives E = 21.4 k.

Run from the repo root: python vectors/generators/erb_scale.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-13}
cases = []
A, B, Q = D("21.4"), D("24.7"), D("4.37")


def rate(f):
    return A * (Q * f / 1000 + 1).log10()


def inverse(e):
    return ((D(10) ** (e / A)) - 1) * 1000 / Q


def band(f):
    return B * (Q * f / 1000 + 1)


def case(op, key, x, fn, why):
    cases.append({"id": f"{op}.{why[0]}", "op": op, "args": {key: x},
                  "expected": float(fn(D(x))), "tol": TOL, "source": why[1]})


assert band(D(0)) == D("24.7") and band(D(1000)) == D("132.639")
assert abs(rate((1000 / Q) * (D(10) ** 2 - 1)) - 2 * A) < D(10) ** -45
for x, name in ((0.0, "zero"), (1000.0, "1khz"), (100.0, "100hz"), (8000.0, "8khz")):
    case("erb_bandwidth", "hz", x, band, (name, f"24.7 (4.37 x {x:g}/1000 + 1), exact in decimal"))
    case("hz_to_erb_rate", "hz", x, rate, (name, f"21.4 log10(4.37 x {x:g}/1000 + 1) in decimal"))
k_one = float((1000 / Q) * 9)
case("hz_to_erb_rate", "hz", k_one, rate,
     ("one_decade", "f = (1000/4.37)(10 - 1) gives E = 21.4 (to the rounding of f)"))
for x, name in ((0.0, "zero"), (21.4, "one_decade"), (10.0, "ten"), (35.0, "thirty_five")):
    case("erb_rate_to_hz", "erb", x, inverse,
         (name, f"(10^({x:g}/21.4) - 1) 1000/4.37 in decimal"))


def err(op, cid, args, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


for op, key in (("hz_to_erb_rate", "hz"), ("erb_rate_to_hz", "erb"), ("erb_bandwidth", "hz")):
    err(op, "negative", {key: -1.0}, "values must be non-negative")
    err(op, "nan", {key: "nan"}, "values must be finite")
    err(op, "inf", {key: "inf"}, "values must be finite")

doc = {
    "schema": 1,
    "suite": "erb_scale",
    "description": "ERB scale, Glasberg & Moore 1990 (conventions: ERB scale; ADR 0160).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "erb_scale.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/erb_scale.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
