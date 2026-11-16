"""Writes vectors/cases/clarity.json, stdlib only.

Clarity and definition (conventions: Clarity and definition; ADR 0172): early energy before
sample N = floor(time fs + 1/2), late from N, as exact hand sums in fractions and, for
h[n] = r^n over L samples, the geometric sums (1 - q^N)/(1 - q) and (q^N - q^L)/(1 - q),
q = r^2, in 50-digit decimal.

Run from the repo root: python vectors/generators/clarity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, op, ir, fs, time, expected, why):
    args = {"impulse_response": ir, "sample_rate": fs}
    if time is not None:
        args["time"] = time
    cases.append({"id": f"clarity.{cid}", "op": op, "args": args, "expected": expected,
                  "tol": TOL, "source": why})


def geometric(r, n, length):
    q = D(r) ** 2
    return (1 - q ** n) / (1 - q), (q ** n - q ** length) / (1 - q)


early, late = geometric("0.99", 80, 400)
add("c80_geometric", "clarity", [0.99 ** n for n in range(400)], 1000.0, None,
    float(10 * (early / late).log10()),
    "h = 0.99^n at 1 kHz, N = 80: 10 log10((1 - q^80)/(q^80 - q^400)), q = 0.9801")
early, late = geometric("0.99", 50, 400)
add("c50_geometric", "clarity", [0.99 ** n for n in range(400)], 1000.0, 0.05,
    float(10 * (early / late).log10()), "the same decay, N = 50")
add("d50_geometric", "definition", [0.99 ** n for n in range(400)], 1000.0, None,
    float(early / (early + late)), "the same decay, N = 50: early over total")
add("hand", "clarity", [2.0, 1.0, 1.0, 1.0], 10.0, 0.2, float(10 * D(5 / 2).log10()),
    "N = floor(2 + 0.5) = 2: early 4 + 1 = 5, late 1 + 1 = 2, so 10 log10(5/2)")
add("hand_definition", "definition", [2.0, 1.0, 1.0, 1.0], 10.0, 0.2, 5 / 7,
    "N = 2: early 5 of total 7")
add("rounding", "definition", [1.0, 1.0, 1.0, 1.0], 10.0, 0.25, 0.75,
    "N = floor(2.5 + 0.5) = 3: sample 3 is late, 3 of 4")
add("complex", "clarity", {"re": [3.0, 0.0, 1.0], "im": [4.0, 1.0, 0.0]}, 1.0, 1.0,
    float(10 * D(25 / 2).log10()), "N = 1: early 25, late 1 + 1 = 2")
add("no_late", "clarity", [1.0, 0.5], 100.0, 0.08, "inf", "N = 8 past the end: all early, +inf")
add("no_late_definition", "definition", [1.0, 0.5], 100.0, 0.08, 1.0, "all early: definition 1")
add("no_early", "clarity", [0.0, 0.0, 1.0], 1.0, 2.0, "-inf", "N = 2: early 0, late 1, -inf")
add("no_early_definition", "definition", [0.0, 0.0, 1.0], 1.0, 2.0, 0.0, "early 0: definition 0")


def err(cid, op, change, why):
    args = {"impulse_response": [1.0, 0.5, 0.25], "sample_rate": 10.0}
    args.update(change)
    cases.append({"id": f"clarity.{cid}", "op": op, "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "clarity", {"impulse_response": []}, "impulse_response must not be empty")
err("all_zero", "clarity", {"impulse_response": [0.0, 0.0]}, "impulse_response must not be all zero")
err("nan", "definition", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("zero_rate", "clarity", {"sample_rate": 0.0}, "sample_rate must be positive")
err("zero_time", "definition", {"time": 0.0}, "time must be positive")
err("inf_time", "clarity", {"time": "inf"}, "time must be finite")
err("rounds_to_zero", "clarity", {"time": 0.04}, "0.04 * 10 + 0.5 = 0.9 rounds down to 0 samples")

doc = {
    "schema": 1,
    "suite": "clarity",
    "description": "Clarity and definition (conventions: Clarity and definition; ADR 0172).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "clarity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/clarity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
