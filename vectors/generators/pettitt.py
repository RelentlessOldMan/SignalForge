"""Writes vectors/cases/pettitt.json, stdlib only.

Pettitt change-point test (conventions: Pettitt change-point test; ADR 0366): every U_t by
the double sum over i <= t < j in integers, the exponent in rationals, then exp in float.

Run from the repo root: python vectors/generators/pettitt.py [--check]
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
    us = [sum((x[j] > x[i]) - (x[j] < x[i]) for i in range(t + 1) for j in range(t + 1, n))
          for t in range(n - 1)]
    k = max(abs(u) for u in us)
    index = next(t for t, u in enumerate(us) if abs(u) == k)
    p = min(1.0, 2 * math.exp(float(Fr(-6 * k * k, n ** 3 + n ** 2))))
    cases.append({"id": f"pettitt.{cid}", "op": "pettitt", "args": {"samples": x},
                  "expected": {"statistic": k, "index": index, "p_value": p}, "tol": TOL,
                  "source": why})
    return us, k, index, p


us, k, index, p = add("step_by_hand", [0.0, 0.0, 1.0, 1.0],
                      "U_0 = 2, U_1 = 4, U_2 = 2: K = 4 at index 1; "
                      "p = 2 exp(-96/80) = 2 exp(-6/5)")
assert us == [2, 4, 2] and (k, index) == (4, 1)
assert abs(p - 2 * math.exp(-1.2)) < 1e-15
us, k, index, p = add("constant", [3.0, 3.0, 3.0], "every U_t is 0: K = 0, index 0, p = 1")
assert (k, index, p) == (0, 0, 1.0)
us, k, index, p = add("drop", [5.0, 6.0, 4.0, 1.0, 2.0, 0.0],
                      "a fall after index 2: U_2 = -9, the largest in size")
assert (k, index) == (9, 2) and us[2] == -9
rng = random.Random(366)
shift = [rng.randint(-16, 16) / 8 + (2.0 if t >= 70 else 0.0) for t in range(120)]
add("shift_in_noise", shift,
    "random eighths from random.Random(366), raised by 2 from sample 70 on")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"pettitt.{cid}", "op": "pettitt", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "pettitt",
    "description": "Pettitt change-point test (conventions: Pettitt change-point test; "
                   "ADR 0366).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pettitt.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pettitt.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
