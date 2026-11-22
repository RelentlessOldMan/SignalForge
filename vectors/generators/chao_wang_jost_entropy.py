"""Writes vectors/cases/chao_wang_jost_entropy.json, stdlib only.

The Chao-Wang-Jost entropy (conventions: the Chao-Wang-Jost entropy; ADR 0562): the
paper's closed form in 60-digit decimal.

Run from the repo root: python vectors/generators/chao_wang_jost_entropy.py [--check]
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
TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    n = sum(v)
    f1 = sum(1 for a in v if a == 1)
    f2 = sum(1 for a in v if a == 2)
    seen = Fr(0)
    for a in v:
        if 1 <= a <= n - 1:
            seen += Fr(a, n) * sum((Fr(1, k) for k in range(a, n)), Fr(0))
    q = dec(seen)
    if f1 > 0:
        big_a = Fr(2 * f2, (n - 1) * f1 + 2 * f2) if f2 > 0 else Fr(2, (n - 1) * (f1 - 1) + 2)
        if big_a != 1:
            one_less = 1 - big_a
            series = sum((one_less**r / r for r in range(1, n)), Fr(0))
            q += dec(Fr(f1, n)) * dec(one_less ** (1 - n)) * (-dec(big_a).ln() - dec(series))
    cases.append(
        {
            "id": f"chao_wang_jost_entropy.{cid}",
            "op": "chao_wang_jost_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert (
    abs(add("two_ones", [1.0, 1.0], "A = 2/3: 1 + 3 ln(3/2) - 1 = 3 ln(3/2)") - 3 * (D(3) / 2).ln())
    < D(10) ** -50
)
assert add("two_twos", [2.0, 2.0], "F1 = 0: 2 (1/2)(1/2 + 1/3) = 5/6") == dec(Fr(5, 6))
assert (
    abs(
        add("one_each", [1.0, 2.0], "A = 1/2: 5/6 + (4/3)(ln 2 - 5/8) = (4/3) ln 2")
        - 4 * D(2).ln() / 3
    )
    < D(10) ** -50
)
assert add("one_kind", [0.0, 4.0], "one kind, no singletons: 0") == 0
add("one_singleton", [1.0, 3.0, 4.0], "F1 = 1, F2 = 0: A = 1, the second part 0")
add("ramp", [1.0, 2.0, 3.0], "N = 6, A = 2/7: A N >= 1")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9, A = 1/9: A N = 1")
add("many_singletons", [1.0] * 12 + [3.0], "N = 15, F2 = 0: A = 2/156, A N < 1")
add("few_singletons", [1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 30.0, 40.0], "N = 81, A = 10/90")
rng = random.Random(562)
x = [float(rng.randint(0, 6)) for _ in range(25)]
add("random", x, "25 whole values from random.Random(562).randint(0, 6)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"chao_wang_jost_entropy.{cid}",
            "op": "chao_wang_jost_entropy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000", samples=[10000.0, 1.0])
err("total_one", "the total must be above 1", samples=[0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "chao_wang_jost_entropy",
    "description": "The Chao-Wang-Jost entropy (conventions: the Chao-Wang-Jost entropy; ADR 0562).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chao_wang_jost_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chao_wang_jost_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
