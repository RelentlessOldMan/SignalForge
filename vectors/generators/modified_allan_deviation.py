"""Writes vectors/cases/modified_allan_deviation.json, stdlib only.

Modified Allan deviation (conventions: Modified Allan deviation; ADR 0328), from the
literature's triple sum over fractional-frequency data, exact in rationals from dyadic samples:
sigma^2 = sum_j [sum_{i=j}^{j+m-1} sum_{k=i}^{i+m-1} (y[k+m] - y[k])]^2 / (2 m^4 (M - 3m + 2)),
j = 0 .. M - 3m + 1; one float square root; tau = m tau0.

Run from the repo root: python vectors/generators/modified_allan_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def mvar(y, m):
    q = [Fr(v) for v in y]
    terms = len(q) - 3 * m + 2
    total = Fr(0)
    for j in range(terms):
        s = sum((q[k + m] - q[k] for i in range(j, j + m) for k in range(i, i + m)), Fr(0))
        total += s * s
    return total / (2 * m**4 * terms)


def add(cid, y, tau0, factors, why):
    expected = {"taus": [float(Fr(m) * Fr(tau0)) for m in factors],
                "deviations": [math.sqrt(mvar(y, m)) for m in factors]}
    cases.append({"id": f"modified_allan_deviation.{cid}", "op": "modified_allan_deviation",
                  "args": {"fractional_frequency": y, "sample_interval": tau0,
                           "averaging_factors": factors},
                  "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("alternating", [1.0, -1.0] * 4, 1.0, [1, 2, 3],
        "y = +-1: m = 1 is the Allan deviation, sqrt 2; m = 2 means all 0, so 0; m = 3 by the "
        "triple sum")
assert e["deviations"][:2] == [math.sqrt(2), 0.0], e
d = Fr(1, 1024)
e = add("drift", [float(d * i * Fr(1, 2)) for i in range(16)], 0.5, [1, 3, 5],
        "a linear drift y = D i tau0, D = 2^-10, tau0 = 1/2: sigma = D tau / sqrt 2 exactly")
for m, s in zip([1, 3, 5], e["deviations"]):
    assert abs(s - float(d) * m * 0.5 / math.sqrt(2)) < 1e-18, (m, s)
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0],
    1e-2, [4, 1, 2, 3], "thirteen arbitrary dyadic samples; m = 4 has three terms (M - 3m + 2)")
add("edge", [0.5, -0.25, 1.0, 0.75, -1.0], 1.0, [2], "five samples, m = 2: 3m = M + 1, one term")


def err(cid, why, **args):
    base = {"fractional_frequency": [0.0, 1.0, 0.5, 2.0, 1.5], "sample_interval": 1.0,
            "averaging_factors": [1]}
    base.update(args)
    cases.append({"id": f"modified_allan_deviation.{cid}", "op": "modified_allan_deviation",
                  "args": base, "error": "invalid_argument", "source": why})


err("factor_too_big", "3 m must be at most the length + 1", averaging_factors=[1, 3])
err("factor_zero", "averaging factors must be at least 1", averaging_factors=[0])
err("no_factors", "averaging_factors must not be empty", averaging_factors=[])
err("interval_negative", "sample_interval must be positive", sample_interval=-1.0)
err("nan", "fractional_frequency must be finite",
    fractional_frequency=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "modified_allan_deviation",
    "description": "Modified Allan deviation (conventions: Modified Allan deviation; ADR 0328).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "modified_allan_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/modified_allan_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
