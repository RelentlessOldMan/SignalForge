"""Writes vectors/cases/hannah_kay_index.json, stdlib only.

The Hannah-Kay index (conventions: the Hannah-Kay index; ADR 0527): the shares of dyadic
values formed exactly, the powers, logarithms and roots in 50-digit decimal.

Run from the repo root: python vectors/generators/hannah_kay_index.py [--check]
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


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, alpha, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    shares = [dec(a / total) for a in v]
    al = D(repr(alpha))
    if al == 1:
        q = (-sum(sh * sh.ln() for sh in shares if sh > 0)).exp()
    else:
        q = sum(sh**al for sh in shares if sh > 0) ** (1 / (1 - al))
    cases.append(
        {
            "id": f"hannah_kay_index.{cid}",
            "op": "hannah_kay_index",
            "args": {"samples": x, "alpha": alpha},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - D(want)) < D("1e-40")


assert near(add("equal_2", [2.0] * 4, 2.0, "four equal shares: 4"), 4)
assert near(add("equal_1", [2.0] * 4, 1.0, "four equal shares: exp(ln 4) = 4"), 4)
assert near(add("equal_half", [2.0] * 4, 0.5, "four equal shares: (4 (1/2))^2 = 4"), 4)
assert near(add("one_holds_all_2", [0.0, 0.0, 0.0, 4.0], 2.0, "one share of 1: 1"), 1)
assert near(add("one_holds_all_1", [0.0, 0.0, 0.0, 4.0], 1.0, "one share of 1, 0 ln 0 = 0: 1"), 1)
assert near(add("ramp_2", [4.0, 1.0, 3.0, 2.0], 2.0, "1/(30/100) = 10/3"), dec(Fr(10, 3)))
assert near(add("three_2", [3.0, 0.0, 1.0], 2.0, "1/(10/16) = 8/5"), dec(Fr(8, 5)))
q = add(
    "halves_3",
    [0.5, 0.25, 0.25, 1.0],
    3.0,
    "shares 1/4, 1/8, 1/8, 1/2: (37/256)^(-1/2) = 16/sqrt(37)",
)
assert near(q, D(16) / D(37).sqrt())
add("ramp_1", [4.0, 1.0, 3.0, 2.0], 1.0, "exp(-sum s ln s), shares 4, 1, 3, 2 tenths")
add("ramp_half", [4.0, 1.0, 3.0, 2.0], 0.5, "(sum sqrt s)^2, shares 4, 1, 3, 2 tenths")
rng = random.Random(527)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, 1.5, "30 values k/8, k from random.Random(527).randint(0, 64); alpha 3/2")
add(
    "huge",
    [1e308, 9e307, 1e300],
    2.0,
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "alpha": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"hannah_kay_index.{cid}",
            "op": "hannah_kay_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("alpha_zero", "alpha must be above 0", alpha=0.0)
err("alpha_negative", "alpha must be above 0", alpha=-1.0)

doc = {
    "schema": 1,
    "suite": "hannah_kay_index",
    "description": "The Hannah-Kay index (conventions: the Hannah-Kay index; ADR 0527).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hannah_kay_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hannah_kay_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
