"""Writes vectors/cases/brillouin_evenness.json, stdlib only.

The Brillouin evenness (conventions: the Brillouin evenness; ADR 0547): the multinomial
coefficients formed exactly, their logarithms in 50-digit decimal.

Run from the repo root: python vectors/generators/brillouin_evenness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import math
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    m = math.factorial(total)
    for a in v:
        m //= math.factorial(a)
    k = sum(1 for a in v if a > 0)
    c, rem = divmod(total, k)
    even = math.factorial(total) // (math.factorial(c) ** (k - rem) * math.factorial(c + 1) ** rem)
    q = D(m).ln() / D(even).ln()
    cases.append(
        {
            "id": f"brillouin_evenness.{cid}",
            "op": "brillouin_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("two_twos", [2.0, 2.0], "already even: 1") == 1
assert add("four_ones", [1.0] * 4, "already even: 1") == 1
assert add("uneven_but_best", [0.0, 2.0, 1.0], "N = 3, k = 2: 1 and 2 is the best: 1") == 1
assert add("two", [3.0, 1.0], "4!/3! = 4 against 4!/(2! 2!) = 6: ln 4 / ln 6") == (
    D(4).ln() / D(6).ln()
)
assert add("five_one", [5.0, 1.0], "6!/5! = 6 against 6!/(3! 3!) = 20: ln 6 / ln 20") == (
    D(6).ln() / D(20).ln()
)
assert add("ramp", [1.0, 2.0, 3.0], "60 against 6!/(2!)^3 = 90: ln 60 / ln 90") == (
    D(60).ln() / D(90).ln()
)
add("larger", [40.0, 25.0, 0.0, 10.0, 25.0], "100!/(40! 25! 10! 25!) against 100!/(25!)^4")
rng = random.Random(547)
x = [float(rng.randint(0, 20)) for _ in range(30)]
add("random", x, "30 whole values from random.Random(547).randint(0, 20)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"brillouin_evenness.{cid}",
            "op": "brillouin_evenness",
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
err("single", "at least 2 values above 0", samples=[4.0])
err("one_positive", "at least 2 values above 0", samples=[0.0, 5.0, 0.0])

doc = {
    "schema": 1,
    "suite": "brillouin_evenness",
    "description": "The Brillouin evenness (conventions: the Brillouin evenness; ADR 0547).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "brillouin_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/brillouin_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
