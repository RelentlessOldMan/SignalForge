"""Writes vectors/cases/theil_index.json, stdlib only.

The Theil index (conventions: the Theil index; ADR 0511): the mean of dyadic values exact in
rationals, each (x/mean) ln(x/mean) in 40-digit decimals, 0 for a value of 0.

Run from the repo root: python vectors/generators/theil_index.py [--check]
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

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    n = len(v)
    mean = sum(v) / n
    q = D(0)
    for a in v:
        if a > 0:
            ratio = a / mean
            rd = D(ratio.numerator) / D(ratio.denominator)
            q += rd * rd.ln()
    q /= n
    cases.append(
        {
            "id": f"theil_index.{cid}",
            "op": "theil_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("single", [5.0], "one value: ln 1 = 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total: ln 4")
assert close(got, D(4).ln())
got = add("two", [1.0, 3.0], "shares 1/2 and 3/2: (3/2 ln(3/2) - 1/2 ln 2)/2")
assert close(got, (D(3) / 2 * (D(3) / 2).ln() - D(2).ln() / 2) / 2)
got = add("halves", [0.0, 2.0, 2.0, 0.0], "two of four hold the total equally: ln 2")
assert close(got, D(2).ln())
got = add("unsorted", [3.0, 0.0, 1.0, 0.0], "mean 1: (3 ln 3 + 0 + 1 ln 1 + 0)/4 = 3 ln 3/4")
assert close(got, 3 * D(3).ln() / 4)
rng = random.Random(511)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(511).randint(0, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"theil_index.{cid}",
            "op": "theil_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "theil_index",
    "description": "The Theil index (conventions: the Theil index; ADR 0511).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "theil_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/theil_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
