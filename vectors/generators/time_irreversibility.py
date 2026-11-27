"""Writes vectors/cases/time_irreversibility.json, stdlib only.

Time irreversibility (conventions: Time irreversibility; ADR 0357): the second and third
moments of the lag increments of dyadic samples exact in rationals; then M3/(M2 sqrt(M2)) in
float.

Run from the repo root: python vectors/generators/time_irreversibility.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, lag, why):
    q = [Fr(v) for v in x]
    d = [b - a for a, b in zip(q, q[lag:])]
    m2 = sum((u * u for u in d), Fr(0)) / len(d)
    m3 = sum((u ** 3 for u in d), Fr(0)) / len(d)
    v = float(m3) / (float(m2) * math.sqrt(float(m2)))
    args = {"samples": x}
    if lag != 1:
        args["lag"] = lag
    cases.append({"id": f"time_irreversibility.{cid}", "op": "time_irreversibility",
                  "args": args, "expected": v, "tol": TOL, "source": why})
    return m2, m3, v


m2, m3, v = add("sawtooth_by_hand", [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0], 1,
                "rise 1, 1, fall 2: increments 1, 1, -2, 1, 1, -2; M2 = 2, M3 = -2, "
                "so -2/(2 sqrt 2) = -1/sqrt 2")
assert (m2, m3) == (2, -2) and abs(v + 1 / math.sqrt(2)) < 1e-15
m2, m3, v = add("reversed_sawtooth", [0.0, 2.0, 1.0, 0.0, 2.0, 1.0, 0.0], 1,
                "the same sawtooth reversed: +1/sqrt 2")
assert abs(v - 1 / math.sqrt(2)) < 1e-15
m2, m3, v = add("symmetric", [0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0], 1,
                "a triangle wave: increments +-1 in equal number, so M3 = 0")
assert v == 0.0
add("lag_3", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75], 3, "fifteen arbitrary dyadic samples, lag 3")
rng = random.Random(357)
walk = [0.0]
for _ in range(299):
    walk.append(walk[-1] + rng.choice([0.25, 0.25, 0.25, -0.75]))
add("skewed_walk", walk, 2, "a 300-step walk of +1/4 three times as often as -3/4, from "
    "random.Random(357), lag 2")


def scaled(cid, base, k, why):
    """Case ``base`` with every sample times 2**k: the statistic is scale-free, and a power of
    2 scales every value exactly, so the expected value is the base case's."""
    c = next(c for c in cases if c["id"] == "time_irreversibility." + base)
    s = 2.0**k
    args = {**c["args"], "samples": [v * s for v in c["args"]["samples"]]}
    assert all(v * s / s == v for v in c["args"]["samples"]), cid
    cases.append({**c, "id": "time_irreversibility." + cid, "args": args, "source": why})


scaled("huge", "sawtooth_by_hand", 1000,
       "case sawtooth_by_hand times 2^1000: squares of the deviations overflow a double, but the "
       "statistic is scale-free, so the same value")
scaled("tiny", "sawtooth_by_hand", -1000,
       "case sawtooth_by_hand times 2^-1000: squares of the deviations underflow to 0, but the "
       "statistic is scale-free, so the same value")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"time_irreversibility.{cid}", "op": "time_irreversibility",
                  "args": base, "error": "invalid_argument", "source": why})


err("lag_zero", "lag must be at least 1", lag=0)
err("lag_too_big", "lag must be at most N - 1", lag=5)
err("constant", "every increment is 0", samples=[2.0, 2.0, 2.0])
err("periodic_lag", "a period-2 record at lag 2 has every increment 0",
    samples=[0.0, 1.0, 0.0, 1.0, 0.0], lag=2)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "time_irreversibility",
    "description": "Time irreversibility (conventions: Time irreversibility; ADR 0357).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "time_irreversibility.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/time_irreversibility.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
