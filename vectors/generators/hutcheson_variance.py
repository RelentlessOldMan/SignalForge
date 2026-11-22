"""Writes vectors/cases/hutcheson_variance.json, stdlib only.

Hutcheson's variance (conventions: Hutcheson's variance; ADR 0556): the sums in 50-digit
decimal.

Run from the repo root: python vectors/generators/hutcheson_variance.py [--check]
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
TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    k = sum(1 for a in v if a > 0)
    lin = D(0)
    sq = D(0)
    for a in v:
        if a > 0:
            p = D(a) / total
            lin += p * p.ln()
            sq += p * p.ln() ** 2
    q = (sq - lin * lin) / total + D(k - 1) / (2 * total * total)
    cases.append(
        {
            "id": f"hutcheson_variance.{cid}",
            "op": "hutcheson_variance",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


LN2 = D(2).ln()
assert add("one_kind", [0.0, 4.0], "one kind: 0 + 0") == 0
assert abs(add("two_twos", [2.0, 2.0], "even shares: 0 + 1/32") - D(1) / 32) < D(10) ** -45
assert (
    abs(
        add("halves_quarters", [1.0, 1.0, 2.0], "Q - L^2 = (ln 2)^2/4: ((ln 2)^2 + 1)/16")
        - (LN2**2 + 1) / 16
    )
    < D(10) ** -45
)
assert abs(add("four_ones", [1.0] * 4, "even shares: 0 + 3/32") - D(3) / 32) < D(10) ** -45
add("ramp", [1.0, 2.0, 3.0], "N = 6, k = 3")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9, k = 4")
add("large", [1000.0, 2000.0, 3000.0, 4000.0], "N = 10000, k = 4")
rng = random.Random(556)
x = [float(rng.randint(0, 9)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(556).randint(0, 9)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hutcheson_variance.{cid}",
            "op": "hutcheson_variance",
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

doc = {
    "schema": 1,
    "suite": "hutcheson_variance",
    "description": "Hutcheson's variance (conventions: Hutcheson's variance; ADR 0556).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hutcheson_variance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hutcheson_variance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
