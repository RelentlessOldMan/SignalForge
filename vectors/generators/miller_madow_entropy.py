"""Writes vectors/cases/miller_madow_entropy.json, stdlib only.

The Miller-Madow entropy (conventions: the Miller-Madow entropy; ADR 0555): each term in
50-digit decimal.

Run from the repo root: python vectors/generators/miller_madow_entropy.py [--check]
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
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    k = sum(1 for a in v if a > 0)
    q = D(k - 1) / (2 * total)
    for a in v:
        if a > 0:
            p = D(a) / total
            q -= p * p.ln()
    cases.append(
        {
            "id": f"miller_madow_entropy.{cid}",
            "op": "miller_madow_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


LN2 = D(2).ln()
assert add("one_kind", [0.0, 4.0], "one kind: 0 + 0") == 0
assert abs(add("two_twos", [2.0, 2.0], "ln 2 + 1/8") - LN2 - D(1) / 8) < D(10) ** -45
assert (
    abs(add("halves_quarters", [1.0, 1.0, 2.0], "(3/2) ln 2 + 2/8") - 3 * LN2 / 2 - D(1) / 4)
    < D(10) ** -45
)
assert abs(add("four_ones", [1.0] * 4, "ln 4 + 3/8") - 2 * LN2 - D(3) / 8) < D(10) ** -45
add("ramp", [1.0, 2.0, 3.0], "N = 6, k = 3")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9, k = 4")
add("large", [1000.0, 2000.0, 3000.0, 4000.0], "N = 10000: the bias term is 3/20000")
rng = random.Random(555)
x = [float(rng.randint(0, 9)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(555).randint(0, 9)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"miller_madow_entropy.{cid}",
            "op": "miller_madow_entropy",
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
    "suite": "miller_madow_entropy",
    "description": "The Miller-Madow entropy (conventions: the Miller-Madow entropy; ADR 0555).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "miller_madow_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/miller_madow_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
