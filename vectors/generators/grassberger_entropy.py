"""Writes vectors/cases/grassberger_entropy.json, stdlib only.

The Grassberger entropy (conventions: the Grassberger entropy; ADR 0559): G from the
digamma definition in 50-digit decimal.

Run from the repo root: python vectors/generators/grassberger_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-12}
EULER = D("0.57721566490153286060651209008240243104215933593992")
LN2 = D(2).ln()
cases = []


def psi_whole(n):
    return -EULER + sum((D(1) / k for k in range(1, n)), D(0))


def psi_half(m):
    """psi(m + 1/2): psi(1/2) = -EULER - 2 ln 2, then psi(z + 1) = psi(z) + 1/z."""
    return -EULER - 2 * LN2 + sum((D(1) / (D(k) + D("0.5")) for k in range(m)), D(0))


def big_g(n):
    if n % 2 == 0:
        diff = psi_half(n // 2) - psi_whole(n // 2)
    else:
        diff = psi_whole((n + 1) // 2) - psi_half(n // 2)
    return psi_whole(n) + (diff if n % 2 == 0 else -diff) / 2


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    q = D(total).ln() - sum((a * big_g(a) for a in v if a > 0), D(0)) / total
    cases.append(
        {
            "id": f"grassberger_entropy.{cid}",
            "op": "grassberger_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert abs(big_g(1) - (-EULER - LN2)) < D(10) ** -45
assert abs(big_g(2) - (2 - EULER - LN2)) < D(10) ** -45
for m in range(1, 6):
    assert abs(big_g(2 * m + 1) - big_g(2 * m)) < D(10) ** -45
    assert abs(big_g(2 * m + 2) - big_g(2 * m) - D(2) / (2 * m + 1)) < D(10) ** -45
assert abs(add("two_ones", [1.0, 1.0], "G(1) = -g - ln 2: 2 ln 2 + g") - 2 * LN2 - EULER) < (
    D(10) ** -45
)
assert (
    abs(add("two_twos", [2.0, 2.0], "G(2) = 2 - g - ln 2: 3 ln 2 + g - 2") - (3 * LN2 + EULER - 2))
    < D(10) ** -45
)
assert (
    abs(
        add("one_kind", [0.0, 4.0], "G(4) = 8/3 - g - ln 2: 3 ln 2 + g - 8/3")
        - (3 * LN2 + EULER - D(8) / 3)
    )
    < D(10) ** -45
)
add("single", [1.0], "N = 1: g + ln 2")
add("ramp", [1.0, 2.0, 3.0], "N = 6")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9")
add("large", [1000.0, 2000.0, 3000.0, 4000.0], "N = 10000")
rng = random.Random(559)
x = [float(rng.randint(0, 9)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(559).randint(0, 9)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"grassberger_entropy.{cid}",
            "op": "grassberger_entropy",
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
    "suite": "grassberger_entropy",
    "description": "The Grassberger entropy (conventions: the Grassberger entropy; ADR 0559).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "grassberger_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/grassberger_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
