"""Writes vectors/cases/fisher_alpha.json, stdlib only.

Fisher's alpha (conventions: Fisher's alpha; ADR 0550): alpha solved from
k = alpha ln(1 + N/alpha) by bisection in 50-digit decimal.

Run from the repo root: python vectors/generators/fisher_alpha.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def solve(k, total):
    lo, hi = D(0), D(2) * D(total) ** 2
    for _ in range(300):
        mid = (lo + hi) / 2
        if mid * (1 + D(total) / mid).ln() < k:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    k = sum(1 for a in v if a > 0)
    q = solve(k, total)
    assert abs(q * (1 + D(total) / q).ln() - k) < D(10) ** -40
    cases.append(
        {
            "id": f"fisher_alpha.{cid}",
            "op": "fisher_alpha",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


add("two", [3.0, 1.0], "k = 2, N = 4")
add("two_twos", [2.0, 2.0], "k = 2, N = 4: as for 3 and 1")
add("ramp", [1.0, 2.0, 3.0], "k = 3, N = 6")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "k = 4, N = 9")
add("dominant", [10.0, 1.0, 1.0, 1.0, 1.0], "k = 5, N = 14")
add("near_k", [1.0, 1.0, 2.0], "k = 3, N = 4: a large alpha")
add("single", [100.0, 0.0], "k = 1, N = 100: a small alpha")
add("large", [400.0, 250.0, 0.0, 100.0, 1.0, 1.0, 3.0], "k = 6, N = 755")
rng = random.Random(550)
x = [float(rng.randint(0, 20)) for _ in range(30)]
add("random", x, "30 whole values from random.Random(550).randint(0, 20)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"fisher_alpha.{cid}",
            "op": "fisher_alpha",
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
err("all_ones", "the total must be above the count of values above 0", samples=[1.0, 1.0])
err("single_one", "the total must be above the count of values above 0", samples=[0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "fisher_alpha",
    "description": "Fisher's alpha (conventions: Fisher's alpha; ADR 0550).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fisher_alpha.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fisher_alpha.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
