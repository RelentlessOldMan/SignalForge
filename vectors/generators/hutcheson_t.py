"""Writes vectors/cases/hutcheson_t.json, stdlib only.

Hutcheson's t (conventions: Hutcheson's t; ADR 0557): H, V and t in 50-digit decimal.

Run from the repo root: python vectors/generators/hutcheson_t.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def parts(x):
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
    return -lin, (sq - lin * lin) / total + D(k - 1) / (2 * total * total)


def add(cid, a, b, why):
    ha, va = parts(a)
    hb, vb = parts(b)
    q = (ha - hb) / (va + vb).sqrt()
    cases.append(
        {
            "id": f"hutcheson_t.{cid}",
            "op": "hutcheson_t",
            "args": {"a": a, "b": b},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


LN2 = D(2).ln()
assert (
    abs(
        add(
            "even_vs_one_kind",
            [2.0, 2.0],
            [0.0, 4.0],
            "H = ln 2, V = 1/32 against 0, 0: 4 sqrt(2) ln 2",
        )
        - 4 * D(2).sqrt() * LN2
    )
    < D(10) ** -45
)
assert (
    abs(
        add("one_kind_vs_even", [4.0], [2.0, 2.0], "the swap: -4 sqrt(2) ln 2")
        + 4 * D(2).sqrt() * LN2
    )
    < D(10) ** -45
)
assert (
    abs(
        add(
            "quarters_vs_halves",
            [1.0, 1.0, 2.0],
            [2.0, 2.0],
            "(ln 2/2)/sqrt(((ln 2)^2 + 1)/16 + 1/32)",
        )
        - LN2 / 2 / ((LN2**2 + 1) / 16 + D(1) / 32).sqrt()
    )
    < D(10) ** -45
)
assert add("same", [1.0, 2.0, 3.0], [3.0, 2.0, 1.0], "the same shares: 0") == 0
add("ramp_vs_mixed", [1.0, 2.0, 3.0], [5.0, 1.0, 1.0, 0.0, 2.0], "N = 6 against N = 9")
add(
    "large",
    [1000.0, 2000.0, 3000.0, 4000.0],
    [2500.0, 2500.0, 2500.0, 2400.0],
    "N = 10000 against N = 9900",
)
rng = random.Random(557)
xa = [float(rng.randint(0, 9)) for _ in range(40)]
xb = [float(rng.randint(0, 4)) for _ in range(30)]
add("random", xa, xb, "40 then 30 whole values from random.Random(557).randint(0, 9), (0, 4)")


def err(cid, why, **args):
    base = {"a": [1.0, 2.0, 3.0], "b": [2.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hutcheson_t.{cid}",
            "op": "hutcheson_t",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("a_empty", "a needs a value", a=[])
err("b_negative", "values must be at least 0", b=[1.0, -0.5, 2.0])
err("a_all_zero", "the total must be positive", a=[0.0, 0.0, 0.0])
err("b_fraction", "values must be whole numbers", b=[1.5, 2.0])
err("a_too_large", "the total must be at most 10 000 000", a=[10000000.0, 1.0])
err("both_one_kind", "V_a + V_b = 0", a=[4.0], b=[0.0, 3.0])

doc = {
    "schema": 1,
    "suite": "hutcheson_t",
    "description": "Hutcheson's t (conventions: Hutcheson's t; ADR 0557).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hutcheson_t.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hutcheson_t.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
