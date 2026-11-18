"""Writes vectors/cases/allan_deviation.json, stdlib only.

Overlapping Allan deviation (conventions: Allan deviation; ADR 0327): for each factor m, the
means of y[k .. k+m-1] and sigma^2 = sum_{j=0}^{M-2m} (ybar_{j+m} - ybar_j)^2 / (2 (M-2m+1)),
exact in rationals from dyadic samples; one float square root; tau = m tau0.

Run from the repo root: python vectors/generators/allan_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def adev(y, m):
    q = [Fr(v) for v in y]
    size = len(q)
    means = [sum(q[k:k + m], Fr(0)) / m for k in range(size - m + 1)]
    terms = size - 2 * m + 1
    return math.sqrt(sum(((means[j + m] - means[j]) ** 2 for j in range(terms)), Fr(0))
                     / (2 * terms))


def add(cid, y, tau0, factors, why):
    expected = {"taus": [float(Fr(m) * Fr(tau0)) for m in factors],
                "deviations": [adev(y, m) for m in factors]}
    cases.append({"id": f"allan_deviation.{cid}", "op": "allan_deviation",
                  "args": {"fractional_frequency": y, "sample_interval": tau0,
                           "averaging_factors": factors},
                  "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("alternating", [1.0, -1.0] * 4, 1.0, [1, 2, 3],
        "y = +-1: m = 1 differences +-2, sigma^2 = 4/2, sqrt 2; m = 2 means all 0, so 0; m = 3 "
        "means +-1/3, differences +-2/3, sigma^2 = 2/9")
assert e["deviations"][:2] == [math.sqrt(2), 0.0], e
assert abs(e["deviations"][2] - math.sqrt(2) / 3) < 1e-16, e
d = Fr(1, 1024)
e = add("drift", [float(d * i * Fr(1, 2)) for i in range(16)], 0.5, [1, 4, 8],
        "a linear drift y = D i tau0, D = 2^-10, tau0 = 1/2: sigma = D tau / sqrt 2 exactly")
for m, s in zip([1, 4, 8], e["deviations"]):
    assert abs(s - float(d) * m * 0.5 / math.sqrt(2)) < 1e-18, (m, s)
add("offset", [1.0 + v / 2**30 for v in (3, -1, 4, 1, -5, 9, 2, -6, 5, 3, -5, 8)], 1e-3,
    [2, 1, 6, 2], "a large offset with small dyadic wander, factors out of order and repeated")
add("short", [0.25, -0.75], 10.0, [1], "two samples: one difference, sigma^2 = 1/2")


def err(cid, why, **args):
    base = {"fractional_frequency": [0.0, 1.0, 0.5, 2.0], "sample_interval": 1.0,
            "averaging_factors": [1]}
    base.update(args)
    cases.append({"id": f"allan_deviation.{cid}", "op": "allan_deviation", "args": base,
                  "error": "invalid_argument", "source": why})


err("factor_too_big", "2 m must be at most the length", averaging_factors=[3])
err("factor_zero", "averaging factors must be at least 1", averaging_factors=[1, 0])
err("no_factors", "averaging_factors must not be empty", averaging_factors=[])
err("interval_zero", "sample_interval must be positive", sample_interval=0.0)
err("one_sample", "needs at least 2 samples", fractional_frequency=[1.0])
err("inf", "fractional_frequency must be finite", fractional_frequency=[0.0, "inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "allan_deviation",
    "description": "Overlapping Allan deviation (conventions: Allan deviation; ADR 0327).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "allan_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/allan_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
