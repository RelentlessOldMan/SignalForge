"""Writes vectors/cases/buishand_range.json, stdlib only.

Buishand range test (conventions: Buishand range test; ADR 0367): dyadic samples whose float
mean is exact (asserted), the partial sums and the variance in rationals, then the square root
and the quotients in float.

Run from the repo root: python vectors/generators/buishand_range.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, why):
    n = len(x)
    mean = sum((Fr(v) for v in x), Fr(0)) / n
    assert Fr(math.fsum(x) / n) == mean, cid
    d = [Fr(v) - mean for v in x]
    var = sum((u * u for u in d), Fr(0)) / n
    sigma = math.sqrt(float(var))
    s, run = [], Fr(0)
    for u in d:
        run += u
        s.append(run)
    top = max(abs(u) for u in s)
    index = next(k for k, u in enumerate(s) if abs(u) == top)
    rng_ = max(Fr(0), max(s)) - min(Fr(0), min(s))
    cases.append({"id": f"buishand_range.{cid}", "op": "buishand_range",
                  "args": {"samples": x},
                  "expected": {"q": float(top) / sigma, "r": float(rng_) / sigma,
                               "index": index},
                  "tol": TOL, "source": why})
    return s, var, index


s, var, index = add("step_by_hand", [0.0, 0.0, 2.0, 2.0],
                    "mean 1, deviations -1, -1, 1, 1: S = -1, -2, -1, 0; sigma 1: q = 2, "
                    "r = 0 - (-2) = 2, index 1")
assert s == [-1, -2, -1, 0] and var == 1 and index == 1
s, var, index = add("both_signs", [1.0, -1.0, 3.0, -3.0],
                    "mean 0: S = 1, 0, 3, 0; sigma sqrt 5: q = r = 3/sqrt 5, index 2")
assert s == [1, 0, 3, 0] and index == 2
rng = random.Random(367)
shift = [rng.randint(-16, 16) / 8 + (1.5 if t >= 40 else 0.0) for t in range(128)]
add("shift_in_noise", shift,
    "128 random eighths from random.Random(367), raised by 3/2 from sample 40 on")


def scaled(cid, base, k, why):
    """Case ``base`` with every sample times 2**k: the statistic is scale-free, and a power of
    2 scales every value exactly, so the expected value is the base case's."""
    c = next(c for c in cases if c["id"] == "buishand_range." + base)
    s = 2.0**k
    args = {**c["args"], "samples": [v * s for v in c["args"]["samples"]]}
    assert all(v * s / s == v for v in c["args"]["samples"]), cid
    cases.append({**c, "id": "buishand_range." + cid, "args": args, "source": why})


scaled("huge", "both_signs", 1000,
       "case both_signs times 2^1000: squares of the deviations overflow a double, but the "
       "statistic is scale-free, so the same value")
scaled("tiny", "both_signs", -1000,
       "case both_signs times 2^-1000: squares of the deviations underflow to 0, but the "
       "statistic is scale-free, so the same value")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"buishand_range.{cid}", "op": "buishand_range", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "buishand_range",
    "description": "Buishand range test (conventions: Buishand range test; ADR 0367).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "buishand_range.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/buishand_range.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
