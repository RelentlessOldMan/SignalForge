"""Writes vectors/cases/centre_time.json, stdlib only.

Centre time (conventions: Centre time; ADR 0173): sum (n/fs)|h[n]|^2 / sum |h[n]|^2 as exact
hand sums in fractions and, for h[n] = r^n over L samples, the closed forms sum q^n =
(1 - q^L)/(1 - q) and sum n q^n = q(1 - L q^(L-1) + (L-1) q^L)/(1 - q)^2, q = r^2, in 50-digit
decimal (the generator checks the closed form against the direct sum).

Run from the repo root: python vectors/generators/centre_time.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as F

getcontext().prec = 50
TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def add(cid, ir, fs, expected, why):
    cases.append({"id": f"centre_time.{cid}", "op": "centre_time",
                  "args": {"impulse_response": ir, "sample_rate": fs},
                  "expected": expected, "tol": TOL, "source": why})


def geometric(r, length, fs):
    q = D(r) ** 2
    total = (1 - q ** length) / (1 - q)
    moment = q * (1 - length * q ** (length - 1) + (length - 1) * q ** length) / (1 - q) ** 2
    direct = sum(n * q ** n for n in range(length))
    assert abs(moment - direct) < D(10) ** -40 * direct, (r, length)
    return float(moment / total / D(fs))


add("geometric", [0.99 ** n for n in range(500)], 1000.0, geometric("0.99", 500, 1000.0),
    "h = 0.99^n, 500 samples at 1 kHz: the closed-form moments of q = 0.9801")
add("geometric_fast", [0.5 ** n for n in range(30)], 48000.0, geometric("0.5", 30, 48000.0),
    "h = 0.5^n, 30 samples at 48 kHz: about q/(1 - q)/fs = 1/(3 fs)")
add("impulse", [1.0, 0.0, 0.0], 8000.0, 0.0, "a unit impulse at index 0: centre time 0")
add("delayed", [0.0, 0.0, 0.0, 2.0], 100.0, 0.03, "all energy at n = 3: 3/100 s")
add("hand", [1.0, 2.0, 1.0], 4.0, float((F(0) + F(4) + F(2)) / 6 / 4),
    "|h|^2 = 1, 4, 1: (0 + 4 + 2)/6 = 1 sample, at 4 Hz 0.25 s")
add("complex", {"re": [3.0, 0.0], "im": [4.0, 5.0]}, 10.0, float(F(25, 50) / 10),
    "|h|^2 = 25, 25: (0 + 25)/50 = 0.5 samples, at 10 Hz 0.05 s")


def err(cid, change, why):
    args = {"impulse_response": [1.0, 0.5], "sample_rate": 10.0}
    args.update(change)
    cases.append({"id": f"centre_time.{cid}", "op": "centre_time", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"impulse_response": []}, "impulse_response must not be empty")
err("all_zero", {"impulse_response": [0.0, 0.0]}, "impulse_response must not be all zero")
err("nan", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("inf_rate", {"sample_rate": "inf"}, "sample_rate must be finite")

doc = {
    "schema": 1,
    "suite": "centre_time",
    "description": "Centre time (conventions: Centre time; ADR 0173).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "centre_time.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/centre_time.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
