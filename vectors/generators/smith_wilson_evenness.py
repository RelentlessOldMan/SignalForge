"""Writes vectors/cases/smith_wilson_evenness.json, stdlib only.

The Smith-Wilson evenness (conventions: the Smith-Wilson evenness; ADR 0534): the
logarithms, the variance and the arctangent in 50-digit decimal, the arctangent by halving
its argument and the Taylor series, pi by Machin's formula.

Run from the repo root: python vectors/generators/smith_wilson_evenness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import math
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 60
TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def atan_series(t):
    # t small: t - t^3/3 + t^5/5 - ...
    term, k, acc = t, 1, D(0)
    while abs(term) > D("1e-70"):
        acc += term / k
        term *= -t * t
        k += 2
    return acc


def atan(t):
    halvings = 0
    while abs(t) > D("0.1"):
        t = t / (1 + (1 + t * t).sqrt())  # atan t = 2 atan(t/(1 + sqrt(1 + t^2)))
        halvings += 1
    return atan_series(t) * 2**halvings


PI = 16 * atan_series(D(1) / 5) - 4 * atan_series(D(1) / 239)
assert abs(float(PI) - math.pi) < 1e-15
assert abs(4 * atan(D(1)) - PI) < D("1e-50")


def add(cid, x, why):
    logs = [D(repr(a)).ln() for a in x]
    m = sum(logs) / len(logs)
    v = sum((g - m) ** 2 for g in logs) / len(logs)
    q = 1 - 2 / PI * atan(v)
    assert abs(float(q) - (1 - 2 / math.pi * math.atan(float(v)))) < 1e-14
    cases.append(
        {
            "id": f"smith_wilson_evenness.{cid}",
            "op": "smith_wilson_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "four equal values, no spread: 1") == 1
assert add("single", [5.0], "one value, no spread: 1") == 1
q = add("two", [1.0, 4.0], "logs 0, 2 ln 2, variance (ln 2)^2: 1 - (2/pi) atan((ln 2)^2)")
assert abs(q - (1 - 2 / PI * atan(D(2).ln() ** 2))) < D("1e-50")
q = add(
    "powers",
    [1.0, 2.0, 4.0, 8.0],
    "logs k ln 2, k 0..3, variance (5/4)(ln 2)^2: 1 - (2/pi) atan(5/4 (ln 2)^2)",
)
assert abs(q - (1 - 2 / PI * atan(D(5) / 4 * D(2).ln() ** 2))) < D("1e-50")
add("ramp", [4.0, 1.0, 3.0, 2.0], "logs of 4, 1, 3, 2")
add("wide", [0.001, 1.0, 1000.0], "logs of 1/1000 (as its double), 1, 1000")
rng = random.Random(534)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(534).randint(1, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"smith_wilson_evenness.{cid}",
            "op": "smith_wilson_evenness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("zero", "values must be above 0", samples=[1.0, 0.0, 2.0])
err("negative", "values must be above 0", samples=[1.0, -0.5, 2.0])

doc = {
    "schema": 1,
    "suite": "smith_wilson_evenness",
    "description": "The Smith-Wilson evenness (conventions: the Smith-Wilson evenness; ADR 0534).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "smith_wilson_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/smith_wilson_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
