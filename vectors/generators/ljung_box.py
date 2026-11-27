"""Writes vectors/cases/ljung_box.json, stdlib only.

Ljung-Box statistic (conventions: Ljung-Box statistic; ADR 0359): the mean, every biased
autocorrelation and Q exact in rationals from dyadic samples.

Run from the repo root: python vectors/generators/ljung_box.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, lags, why):
    q = [Fr(v) for v in x]
    n = len(q)
    mean = sum(q, Fr(0)) / n
    d = [u - mean for u in q]
    c0 = sum((u * u for u in d), Fr(0))
    total = Fr(0)
    for k in range(1, lags + 1):
        rho = sum((d[t] * d[t + k] for t in range(n - k)), Fr(0)) / c0
        total += rho * rho / (n - k)
    v = n * (n + 2) * total
    cases.append({"id": f"ljung_box.{cid}", "op": "ljung_box",
                  "args": {"samples": x, "lags": lags}, "expected": float(v), "tol": TOL,
                  "source": why})
    return v


v = add("alternating_by_hand", [1.0, -1.0, 1.0, -1.0], 1,
        "mean 0, c0 = 4, lag-1 sum -3: rho = -3/4; Q = 4*6*(9/16)/3 = 9/2")
assert v == Fr(9, 2)
v = add("alternating_two_lags", [1.0, -1.0, 1.0, -1.0], 2,
        "adds rho_2 = 2/4 = 1/2: Q = 24*(9/48 + 1/8) = 15/2")
assert v == Fr(15, 2)
add("ramp", [float(t) for t in range(12)], 5, "a ramp of twelve: strongly correlated, five lags")
rng = random.Random(359)
noise = [rng.randint(-100, 100) / 32 for _ in range(400)]
for h in [1, 10, 40]:
    add(f"noise_h{h}", noise, h, f"400 random 32nds from random.Random(359), {h} lags")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "lags": 2}
    base.update(args)
    cases.append({"id": f"ljung_box.{cid}", "op": "ljung_box", "args": base,
                  "error": "invalid_argument", "source": why})


err("lags_zero", "lags must be at least 1", lags=0)
err("lags_too_many", "lags must be at most N - 1", lags=5)
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

def scaled(cid, base, k, why):
    """Case ``base`` with the samples times 2**k: the measure is unchanged by a scale,
    and a power of 2 scales every value exactly, so the expected value is the base
    case's."""
    c = next(c for c in cases if c["id"] == "ljung_box." + base)
    s = 2.0**k
    assert all(u * s / s == u for u in c["args"]["samples"]), cid
    args = {**c["args"], "samples": [u * s for u in c["args"]["samples"]]}
    cases.append({**c, "id": "ljung_box." + cid, "args": args, "source": why})


scaled("huge", "ramp", 1000,
       "case ramp times 2^1000: squares of the samples overflow a double, but the "
       "measure is unchanged by a scale, so the same value")
scaled("tiny", "ramp", -1000,
       "case ramp times 2^-1000: squares of the samples underflow to 0, but the "
       "measure is unchanged by a scale, so the same value")


doc = {
    "schema": 1,
    "suite": "ljung_box",
    "description": "Ljung-Box statistic (conventions: Ljung-Box statistic; ADR 0359).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ljung_box.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ljung_box.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
