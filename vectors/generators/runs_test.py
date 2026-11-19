"""Writes vectors/cases/runs_test.json, stdlib only.

Runs test (conventions: Runs test; ADR 0361): dyadic samples whose float mean is exact
(asserted), labels by exact comparison, the mean and variance of the run count in rationals,
then the square root and the quotient in float.

Run from the repo root: python vectors/generators/runs_test.py [--check]
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
    mean = sum((Fr(v) for v in x), Fr(0)) / len(x)
    assert Fr(math.fsum(x) / len(x)) == mean, cid
    labels = [Fr(v) > mean for v in x if Fr(v) != mean]
    n1 = sum(labels)
    n2 = len(labels) - n1
    n = n1 + n2
    runs = 1 + sum(1 for a, b in zip(labels, labels[1:]) if a != b)
    p = 2 * n1 * n2
    mu = Fr(p, n) + 1
    var = Fr(p * (p - n), n * n * (n - 1))
    z = float(runs - mu) / math.sqrt(float(var))
    cases.append({"id": f"runs_test.{cid}", "op": "runs_test", "args": {"samples": x},
                  "expected": {"runs": runs, "z": z}, "tol": TOL, "source": why})
    return runs, mu, var, z


runs, mu, var, z = add("by_hand", [1.0, 2.0, -1.0, -2.0, 3.0, -3.0],
                       "mean 0: + + - - + -, four runs; n1 = n2 = 3: mu = 4, so z = 0")
assert (runs, mu, z) == (4, 4, 0.0) and var == Fr(6, 5)
runs, mu, var, z = add("mean_dropped", [0.0, 1.0, -1.0, 0.0, 1.0, -1.0, 0.0],
                       "mean 0: the three zeros drop; + - + -: four runs; n = 4: mu = 3, "
                       "var = 8*4/(16*3) = 2/3")
assert (runs, mu, var) == (4, 3, Fr(2, 3))
runs, mu, var, z = add("trend", [float(t) for t in range(9)],
                       "a ramp of nine: the mean 4 drops, then two runs of four")
assert runs == 2
runs, mu, var, z = add("alternating", [1.0, -1.0] * 8, "sixteen alternating samples: 16 runs")
assert runs == 16
rng = random.Random(361)
noise = [rng.randint(-64, 64) / 16 for _ in range(256)]
add("noise", noise, "256 random sixteenths from random.Random(361)")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"runs_test.{cid}", "op": "runs_test", "args": base,
                  "error": "invalid_argument", "source": why})


err("constant", "every sample equals the mean", samples=[2.0, 2.0, 2.0])
err("two_labels", "one of each label: 2 n1 n2 = n, so the variance is 0",
    samples=[1.0, -1.0])
err("empty", "samples must not be empty", samples=[])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "runs_test",
    "description": "Runs test (conventions: Runs test; ADR 0361).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "runs_test.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/runs_test.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
