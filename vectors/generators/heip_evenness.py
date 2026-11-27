"""Writes vectors/cases/heip_evenness.json, stdlib only.

Heip's evenness (conventions: Heip's evenness; ADR 0531): the shares of dyadic values
formed exactly, the logarithms and exponential in 50-digit decimal.

Run from the repo root: python vectors/generators/heip_evenness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 50
TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    shares = [D((a / total).numerator) / D((a / total).denominator) for a in v]
    q = ((-sum(sh * sh.ln() for sh in shares if sh > 0)).exp() - 1) / (len(v) - 1)
    cases.append(
        {
            "id": f"heip_evenness.{cid}",
            "op": "heip_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - D(want)) < D("1e-40")


assert near(add("equal", [2.0] * 4, "four equal shares: (exp(ln 4) - 1)/3 = 1"), 1)
assert near(add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one share of 1: (1 - 1)/3 = 0"), 0)
assert near(
    add("halves", [0.5, 0.25, 0.25, 1.0], "shares 1/4, 1/8, 1/8, 1/2: (2^(7/4) - 1)/3"),
    (D(2) ** (D(7) / D(4)) - 1) / 3,
)
assert near(
    add("one_zero", [0.0, 2.0, 2.0, 2.0, 2.0], "four equal shares of five: (4 - 1)/4 = 3/4"),
    D(3) / D(4),
)
assert near(
    add("two", [3.0, 1.0], "shares 3/4, 1/4: 4/3^(3/4) - 1"), D(4) / D(3) ** (D(3) / D(4)) - 1
)
add("ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 1, 3, 2 tenths")
add("three", [3.0, 0.0, 1.0], "shares 3/4, 0, 1/4 over 2")
rng = random.Random(531)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(531).randint(0, 64)")
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
            "id": f"heip_evenness.{cid}",
            "op": "heip_evenness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs at least 2 values", samples=[])
err("single", "the record needs at least 2 values", samples=[5.0])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "heip_evenness",
    "description": "Heip's evenness (conventions: Heip's evenness; ADR 0531).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "heip_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/heip_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
