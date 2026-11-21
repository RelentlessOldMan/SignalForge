"""Writes vectors/cases/atkinson_index.json, stdlib only.

The Atkinson index (conventions: the Atkinson index; ADR 0515): each ratio of a dyadic value
to the mean exact in rationals, each power exp(p ln r) in 40-digit decimals.

Run from the repo root: python vectors/generators/atkinson_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as Fr

getcontext().prec = 40

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, eps, why):
    v = [Fr(a) for a in x]
    n = len(v)
    mean = sum(v) / n
    logs = [dec(a / mean).ln() for a in v]
    if eps == 1:
        q = 1 - (sum(logs) / n).exp()
    else:
        p = 1 - dec(Fr(eps))
        m = sum((p * g).exp() for g in logs) / n
        q = 1 - (m.ln() / p).exp()
    cases.append(
        {
            "id": f"atkinson_index.{cid}",
            "op": "atkinson_index",
            "args": {"samples": x, "epsilon": eps},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("equal", [2.0, 2.0, 2.0], 2.0, "every value equal: 0")
assert close(got, 0)
got = add("no_aversion", [1.0, 1.0, 4.0], 0.0, "epsilon 0: one less the mean over the mean, 0")
assert close(got, 0)
got = add("geometric", [1.0, 2.0, 4.0], 1.0, "geometric mean 2, mean 7/3: 1 - 6/7 = 1/7")
assert close(got, D(1) / 7)
got = add("geometric_two", [1.0, 3.0], 1.0, "geometric mean sqrt 3, mean 2: 1 - sqrt 3/2")
assert close(got, 1 - D(3).sqrt() / 2)
got = add("harmonic", [1.0, 3.0], 2.0, "harmonic mean 3/2, mean 2: 1 - 3/4 = 1/4")
assert close(got, D(1) / 4)
got = add(
    "half", [1.0, 4.0], 0.5, "ratios 2/5, 8/5: ((sqrt(2/5) + 2 sqrt(2/5))/2)^2 = 9/10, so 1/10"
)
assert close(got, D(1) / 10)
got = add(
    "three",
    [1.0, 2.0, 4.0],
    3.0,
    "mean of (7/3)^2/x^2 = (7/3)^2 7/16, to the -1/2: 12/(7 sqrt 7), so 1 - 12/(7 sqrt 7)",
)
assert close(got, 1 - 12 / (7 * D(7).sqrt()))
rng = random.Random(515)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, 1.5, "30 values k/8, k from random.Random(515).randint(1, 64); epsilon 3/2")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "epsilon": 1.0}
    base.update(args)
    cases.append(
        {
            "id": f"atkinson_index.{cid}",
            "op": "atkinson_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("zero", "values must be greater than 0", samples=[1.0, 0.0, 2.0])
err("negative", "values must be greater than 0", samples=[1.0, -0.5, 2.0])
err("negative_epsilon", "epsilon must be at least 0", epsilon=-0.5)

doc = {
    "schema": 1,
    "suite": "atkinson_index",
    "description": "The Atkinson index (conventions: the Atkinson index; ADR 0515).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "atkinson_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/atkinson_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
