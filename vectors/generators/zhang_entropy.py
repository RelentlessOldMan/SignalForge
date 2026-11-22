"""Writes vectors/cases/zhang_entropy.json, stdlib only.

Zhang's entropy (conventions: Zhang's entropy; ADR 0561): the definition's product and sum
to v = N - 1 in exact rationals.

Run from the repo root: python vectors/generators/zhang_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    q = Fr(0)
    for a in v:
        if a > 0:
            prod = Fr(1)
            for step in range(1, total):
                prod *= 1 - Fr(a - 1, total - step)
                q += Fr(a, total) * prod / step
    cases.append(
        {
            "id": f"zhang_entropy.{cid}",
            "op": "zhang_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("two_ones", [1.0, 1.0], "N = 2: 2 (1/2)(1) = 1") == 1
assert add("two_twos", [2.0, 2.0], "N = 4: 2 (1/2)(2/3 + (1/3)/2) = 5/6") == Fr(5, 6)
assert add("one_kind", [0.0, 4.0], "every product meets a 0 factor: 0") == 0
add("ramp", [1.0, 2.0, 3.0], "N = 6")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9")
add("repeats", [3.0, 3.0, 3.0, 1.0, 1.0], "N = 11, repeated values")
add("large", [10.0, 20.0, 30.0, 40.0], "N = 100")
rng = random.Random(561)
x = [float(rng.randint(0, 6)) for _ in range(25)]
add("random", x, "25 whole values from random.Random(561).randint(0, 6)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"zhang_entropy.{cid}",
            "op": "zhang_entropy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000", samples=[10000.0, 1.0])
err("total_one", "the total must be above 1", samples=[0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "zhang_entropy",
    "description": "Zhang's entropy (conventions: Zhang's entropy; ADR 0561).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "zhang_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/zhang_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
