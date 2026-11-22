"""Writes vectors/cases/jackknife_entropy.json, stdlib only.

The jackknife Shannon entropy (conventions: the jackknife Shannon entropy; ADR 0558): each
reduced record's plug-in entropy formed directly in 50-digit decimal.

Run from the repo root: python vectors/generators/jackknife_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-10, "rel": 1e-11}
cases = []


def plug(v):
    total = sum(v)
    return -sum((D(a) / total * (D(a) / total).ln() for a in v if a > 0), D(0))


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    acc = D(0)
    for i, a in enumerate(v):
        if a > 0:
            acc += a * plug(v[:i] + [a - 1] + v[i + 1 :])
    q = total * plug(v) - D(total - 1) / total * acc
    cases.append(
        {
            "id": f"jackknife_entropy.{cid}",
            "op": "jackknife_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("one_kind", [0.0, 4.0], "one kind: every H is 0") == 0
assert (
    abs(add("two_ones", [1.0, 1.0], "H = ln 2, each H_-i = 0: 2 ln 2") - 2 * D(2).ln())
    < D(10) ** -45
)
assert (
    abs(
        add("two_twos", [2.0, 2.0], "4 ln 2 - (3/4)(4 ln 3 - (8/3) ln 2) = 3 ln(4/3)")
        - 3 * (D(4) / 3).ln()
    )
    < D(10) ** -45
)
add("ramp", [1.0, 2.0, 3.0], "N = 6")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9")
add("large", [1000.0, 2000.0, 3000.0, 4000.0], "N = 10000")
rng = random.Random(558)
x = [float(rng.randint(0, 9)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(558).randint(0, 9)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"jackknife_entropy.{cid}",
            "op": "jackknife_entropy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000 000", samples=[10000000.0, 1.0])
err("total_one", "the total must be above 1", samples=[0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "jackknife_entropy",
    "description": "The jackknife Shannon entropy (conventions: the jackknife Shannon entropy; ADR 0558).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "jackknife_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/jackknife_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
