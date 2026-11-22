"""Writes vectors/cases/chao_shen_entropy.json, stdlib only.

The Chao-Shen entropy (conventions: the Chao-Shen entropy; ADR 0554): each term in
50-digit decimal, the power as an exact integer power.

Run from the repo root: python vectors/generators/chao_shen_entropy.py [--check]
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
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    f1 = sum(1 for a in v if a == 1)
    if f1 == total:
        f1 = total - 1
    c = 1 - Fr(f1, total)
    q = D(0)
    for a in v:
        if a > 0:
            share = c * Fr(a, total)
            d = D(share.numerator) / D(share.denominator)
            q -= d * d.ln() / (1 - (1 - d) ** total)
    cases.append(
        {
            "id": f"chao_shen_entropy.{cid}",
            "op": "chao_shen_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


LN2 = D(2).ln()
assert add("one_kind", [0.0, 4.0], "one kind: C = 1, a = 1: 0") == 0
assert (
    abs(
        add("two_twos", [2.0, 2.0], "C = 1, a = 1/2: 2 (ln 2/2)/(15/16) = (16/15) ln 2")
        - 16 * LN2 / 15
    )
    < D(10) ** -45
)
assert (
    abs(
        add("two_ones", [1.0, 1.0], "F1 = N, taken as 1: C = 1/2, a = 1/4: (16/7) ln 2")
        - 16 * LN2 / 7
    )
    < D(10) ** -45
)
add("single", [1.0], "N = 1, F1 taken as 0: a = 1: 0")
add("ramp", [1.0, 1.0, 2.0, 3.0], "N = 7, F1 = 2: C = 5/7")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9, F1 = 2: C = 7/9")
add("no_singletons", [10.0, 20.0, 30.0, 40.0], "C = 1: the plug-in shares over 1 - (1 - p)^100")
rng = random.Random(554)
x = [float(rng.randint(0, 6)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(554).randint(0, 6)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"chao_shen_entropy.{cid}",
            "op": "chao_shen_entropy",
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
    "suite": "chao_shen_entropy",
    "description": "The Chao-Shen entropy (conventions: the Chao-Shen entropy; ADR 0554).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chao_shen_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chao_shen_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
