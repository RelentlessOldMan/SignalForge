"""Writes vectors/cases/pielou_evenness.json, stdlib only.

Pielou's evenness (conventions: Pielou's evenness; ADR 0528): the shares of dyadic values
formed exactly, the logarithms in 50-digit decimal.

Run from the repo root: python vectors/generators/pielou_evenness.py [--check]
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
TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    shares = [D((a / total).numerator) / D((a / total).denominator) for a in v]
    q = -sum(sh * sh.ln() for sh in shares if sh > 0) / D(len(v)).ln()
    cases.append(
        {
            "id": f"pielou_evenness.{cid}",
            "op": "pielou_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - D(want)) < D("1e-40")


assert near(add("equal", [2.0] * 4, "four equal shares: ln 4/ln 4 = 1"), 1)
assert near(add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one share of 1: 0"), 0)
assert near(
    add("halves", [0.5, 0.25, 0.25, 1.0], "shares 1/4, 1/8, 1/8, 1/2: (7/4) ln 2/ln 4 = 7/8"),
    D(7) / D(8),
)
assert near(
    add("one_zero", [0.0, 2.0, 2.0, 2.0, 2.0], "four equal shares of five: ln 4/ln 5"),
    D(4).ln() / D(5).ln(),
)
add("two", [3.0, 1.0], "shares 3/4, 1/4: -(3/4 ln 3/4 + 1/4 ln 1/4)/ln 2")
add("ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 1, 3, 2 tenths")
add("three", [3.0, 0.0, 1.0], "shares 3/4, 0, 1/4 over ln 3")
rng = random.Random(528)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(528).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"pielou_evenness.{cid}",
            "op": "pielou_evenness",
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
    "suite": "pielou_evenness",
    "description": "Pielou's evenness (conventions: Pielou's evenness; ADR 0528).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pielou_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pielou_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
