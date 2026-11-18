"""Writes vectors/cases/time_deviation.json, stdlib only.

Time deviation (conventions: Time deviation; ADR 0331): TDEV^2 = tau^2 Mod sigma^2 / 3, the
modified Allan variance from the literature's triple sum
sum_j [sum_{i=j}^{j+m-1} sum_{k=i}^{i+m-1} (y[k+m] - y[k])]^2 / (2 m^4 (M - 3m + 2)), all exact
in rationals from dyadic samples; one float square root; tau = m tau0.

Run from the repo root: python vectors/generators/time_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-18, "rel": 1e-12}
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
    taus = [Fr(m) * Fr(tau0) for m in factors]
    expected = {"taus": [float(t) for t in taus],
                "deviations": [math.sqrt(t * t * mvar(y, m) / 3) for t, m in zip(taus, factors)]}
    cases.append({"id": f"time_deviation.{cid}", "op": "time_deviation",
                  "args": {"fractional_frequency": y, "sample_interval": tau0,
                           "averaging_factors": factors},
                  "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("alternating", [1.0, -1.0] * 4, 1.0, [1, 2],
        "y = +-1, tau0 = 1: m = 1 MDEV sqrt 2, so TDEV sqrt(2/3); m = 2 gives 0")
assert abs(e["deviations"][0] - math.sqrt(2 / 3)) < 1e-15 and e["deviations"][1] == 0.0, e
add("ppb", [v / 2**30 for v in (3, -1, 4, 1, -5, 9, 2, -6, 5, 3, -5, 8, 0, -2)], 0.125,
    [1, 2, 4], "parts-per-billion wander, tau0 = 1/8 s")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0],
    1e-2, [4, 3], "thirteen arbitrary dyadic samples")


def err(cid, why, **args):
    base = {"fractional_frequency": [0.0, 1.0, 0.5, 2.0, 1.5], "sample_interval": 1.0,
            "averaging_factors": [1]}
    base.update(args)
    cases.append({"id": f"time_deviation.{cid}", "op": "time_deviation", "args": base,
                  "error": "invalid_argument", "source": why})


err("factor_too_big", "3 m must be at most the length + 1", averaging_factors=[3])
err("no_factors", "averaging_factors must not be empty", averaging_factors=[])
err("interval_zero", "sample_interval must be positive", sample_interval=0.0)

doc = {
    "schema": 1,
    "suite": "time_deviation",
    "description": "Time deviation (conventions: Time deviation; ADR 0331).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "time_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/time_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
