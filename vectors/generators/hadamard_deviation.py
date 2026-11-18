"""Writes vectors/cases/hadamard_deviation.json, stdlib only.

Overlapping Hadamard deviation (conventions: Hadamard deviation; ADR 0329): the means of
y[k .. k+m-1] and sigma^2 = sum_{j=0}^{M-3m} (ybar_{j+2m} - 2 ybar_{j+m} + ybar_j)^2
/ (6 (M - 3m + 1)), exact in rationals from dyadic samples; one float square root; tau = m tau0.

Run from the repo root: python vectors/generators/hadamard_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def hvar(y, m):
    q = [Fr(v) for v in y]
    size = len(q)
    means = [sum(q[k:k + m], Fr(0)) / m for k in range(size - m + 1)]
    terms = size - 3 * m + 1
    return sum(((means[j + 2 * m] - 2 * means[j + m] + means[j]) ** 2 for j in range(terms)),
               Fr(0)) / (6 * terms)


def add(cid, y, tau0, factors, why):
    expected = {"taus": [float(Fr(m) * Fr(tau0)) for m in factors],
                "deviations": [math.sqrt(hvar(y, m)) for m in factors]}
    cases.append({"id": f"hadamard_deviation.{cid}", "op": "hadamard_deviation",
                  "args": {"fractional_frequency": y, "sample_interval": tau0,
                           "averaging_factors": factors},
                  "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("alternating", [1.0, -1.0] * 4, 1.0, [1, 2],
        "y = +-1: m = 1 second differences +-4, sigma^2 = 16/6; m = 2 means all 0, so 0")
assert abs(e["deviations"][0] - math.sqrt(16 / 6)) < 1e-15 and e["deviations"][1] == 0.0, e
d = Fr(1, 1024)
e = add("drift", [float(Fr(3, 8) + d * i * Fr(1, 2)) for i in range(15)], 0.5, [1, 2, 5],
        "an offset plus a linear drift: every second difference is 0")
assert e["deviations"] == [0.0, 0.0, 0.0], e
add("quadratic", [float(Fr(i * i, 64)) for i in range(12)], 2.0, [1, 3, 4],
    "y = i^2/64: second differences of the means are 2 m^2 / 64, sigma = 2 m^2 / (64 sqrt 6)")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0],
    1e-2, [4, 1, 2], "thirteen arbitrary dyadic samples; m = 4 has two terms")


def err(cid, why, **args):
    base = {"fractional_frequency": [0.0, 1.0, 0.5, 2.0, 1.5], "sample_interval": 1.0,
            "averaging_factors": [1]}
    base.update(args)
    cases.append({"id": f"hadamard_deviation.{cid}", "op": "hadamard_deviation", "args": base,
                  "error": "invalid_argument", "source": why})


err("factor_too_big", "3 m must be at most the length", averaging_factors=[2])
err("factor_zero", "averaging factors must be at least 1", averaging_factors=[0])
err("no_factors", "averaging_factors must not be empty", averaging_factors=[])
err("two_samples", "needs at least 3 samples", fractional_frequency=[1.0, 2.0])
err("interval_inf", "sample_interval must be finite", sample_interval="inf")

doc = {
    "schema": 1,
    "suite": "hadamard_deviation",
    "description": "Overlapping Hadamard deviation (conventions: Hadamard deviation; ADR 0329).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hadamard_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hadamard_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
