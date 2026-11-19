"""Writes vectors/cases/snht.json, stdlib only.

Standard normal homogeneity test (conventions: Standard normal homogeneity test; ADR 0368):
dyadic samples whose float mean is exact (asserted); every T_k = k z1^2 + (N - k) z2^2 from
the means of the two parts, exactly in rationals.

Run from the repo root: python vectors/generators/snht.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []


def add(cid, x, why):
    n = len(x)
    q = [Fr(v) for v in x]
    mean = sum(q, Fr(0)) / n
    assert Fr(math.fsum(x) / n) == mean, cid
    var = sum(((u - mean) ** 2 for u in q), Fr(0)) / n
    ts = []
    for k in range(1, n):
        # z = (x - mean)/sigma, so z-bar squared is (mean of x - mean)^2 / var.
        m1 = sum(q[:k], Fr(0)) / k - mean
        m2 = sum(q[k:], Fr(0)) / (n - k) - mean
        ts.append((k * m1 * m1 + (n - k) * m2 * m2) / var)
    top = max(ts)
    index = ts.index(top)
    cases.append({"id": f"snht.{cid}", "op": "snht", "args": {"samples": x},
                  "expected": {"statistic": float(top), "index": index}, "tol": TOL,
                  "source": why})
    return ts, index


ts, index = add("step_by_hand", [0.0, 0.0, 2.0, 2.0],
                "mean 1, sigma 1: z = -1, -1, 1, 1; T_2 = 2*1 + 2*1 = 4, the largest, "
                "so index 1")
assert ts[1] == 4 and index == 1
ts, index = add("one_outlier", [0.0, 0.0, 0.0, 4.0],
                "mean 1, sigma^2 3: T_3 = (3*1 + 1*9)/3 = 4 at index 2")
assert ts[2] == 4 and index == 2
rng = random.Random(368)
shift = [rng.randint(-16, 16) / 8 + (1.0 if t >= 90 else 0.0) for t in range(128)]
add("shift_in_noise", shift,
    "128 random eighths from random.Random(368), raised by 1 from sample 90 on")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"snht.{cid}", "op": "snht", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "snht",
    "description": "Standard normal homogeneity test (conventions: Standard normal "
                   "homogeneity test; ADR 0368).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "snht.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/snht.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
