"""Writes vectors/cases/tsallis_evenness.json, stdlib only.

Tsallis evenness (conventions: Tsallis evenness; ADR 0569): exact shares and
(1 - sum p^q)/(1 - K^(1-q)), or H/ln K at q = 1, in 60-digit decimal.

Run from the repo root: python vectors/generators/tsallis_evenness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 60
TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, q, why):
    xs = [Fr(a) for a in x]
    total = sum(xs, Fr(0))
    shares = [dec(a / total) for a in xs if a > 0]
    qq = dec(Fr(q))
    k = D(len(shares))
    if q == 1:
        v = -sum(p * p.ln() for p in shares) / k.ln()
    else:
        s = sum(((qq * p.ln()).exp() for p in shares), D(0))
        v = (1 - s) / (1 - ((1 - qq) * k.ln()).exp())
    cases.append(
        {
            "id": f"tsallis_evenness.{cid}",
            "op": "tsallis_evenness",
            "args": {"samples": x, "order": q},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("even_pair", [1.0, 1.0], 2.0, "two equal shares: 1 at any order"), 1)
assert near(add("richness", [0.0, 3.0, 5.0], 0.0, "q = 0: (K - 1)/(K - 1) = 1"), 1)
assert near(add("simpson", [1.0, 1.0, 2.0], 2.0, "(5/8)/(2/3) = 15/16"), D(15) / 16)
assert near(
    add("shannon", [1.0, 1.0, 2.0], 1.0, "(3/2) ln 2/ln 3"), D("1.5") * D(2).ln() / D(3).ln()
)
assert near(
    add("half", [1.0, 3.0], 0.5, "(sqrt 3 - 1)/(2 (sqrt 2 - 1))"),
    (D(3).sqrt() - 1) / (2 * (D(2).sqrt() - 1)),
)
add("near_one", [2.0, 0.5, 3.25, 1.0], 1.000001, "q just above 1")
add("edge", [2.0, 0.5, 3.25, 1.0], 1.5, "q = 1.5")
add("large", [2.0, 0.5, 3.25, 1.0, 0.0], 250.0, "q = 250")
add("small_order", [2.0, 0.5, 3.25, 1.0, 0.0], 0.1, "q = 0.1, a zero value left out of K")
rng = random.Random(569)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add("random", x, 2.5, "30 values from random.Random(569).uniform(0, 5), 3 places, q = 2.5")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "order": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"tsallis_evenness.{cid}",
            "op": "tsallis_evenness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("negative_order", "the order must be at least 0", order=-0.5)
err("one_kind", "the maximum is 0 with one kind", samples=[0.0, 4.0, 0.0])

doc = {
    "schema": 1,
    "suite": "tsallis_evenness",
    "description": "Tsallis evenness (conventions: Tsallis evenness; ADR 0569).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tsallis_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tsallis_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
