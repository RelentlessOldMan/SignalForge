"""Writes vectors/cases/savage_selection_ratio.json, stdlib only.

Savage's selection ratio (conventions: Savage's selection ratio; ADR 0606): the shares of
each record and p/r for each kind with fractions.

Run from the repo root: python vectors/generators/savage_selection_ratio.py [--check]
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
TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, available, why):
    xs = [Fr(a) for a in x]
    avs = [Fr(c) for c in available]
    sx = sum(xs)
    sa = sum(avs)
    w = [(a / sx) / (c / sa) for a, c in zip(xs, avs)]
    f = w
    v = [D(fi.numerator) / D(fi.denominator) for fi in f]
    cases.append(
        {
            "id": f"savage_selection_ratio.{cid}",
            "op": "savage_selection_ratio",
            "args": {"x": x, "available": available},
            "expected": [float(vi) + 0.0 for vi in v],
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add(
    "as_available", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "use as availability: 1 for each kind"
) == [1, 1, 1]
assert add("even_use", [1.0, 1.0], [1.0, 3.0], "halves on 1/4, 3/4: 2, 2/3") == [2, Fr(2, 3)]
assert add("one_kind_used", [1.0, 0.0], [1.0, 3.0], "1, 0 on 1/4, 3/4: 4, 0") == [4, 0]
assert add(
    "uneven", [2.0, 1.0, 1.0], [1.0, 2.0, 1.0], "1/2, 1/4, 1/4 on 1/4, 1/2, 1/4: 2, 1/2, 1"
) == [2, Fr(1, 2), 1]
assert add("one_kind", [2.0], [5.0], "one kind: 1") == [1]
assert add(
    "huge", [1e308, 1e308], [1e308, 1e308], "the sums would overflow: halves on halves: 1, 1"
) == [1, 1]
f = add(
    "tiny",
    [5e-324, 1.0],
    [1.0, 1.0],
    "the smallest double counts: 1e-323/(1 + 5e-324), 2/(1 + 5e-324)",
)
assert f == [2 * Fr(5e-324) / (1 + Fr(5e-324)), 2 / (1 + Fr(5e-324))]
rng = random.Random(606)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
x[0] = 1.0
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    available,
    "x then available, 25 values each from random.Random(606)"
    ".choice([0, 0, 1, 2.5]) with x[0] = 1, and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"savage_selection_ratio.{cid}",
            "op": "savage_selection_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], available=[])
err("negative", "values must be at least 0", x=[1.0, -0.5, 2.0])
err("all_zero", "a record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", available=[1.0, 2.0])
err("unavailable", "available must be above 0 everywhere", available=[1.0, 0.0, 1.0])
err("underflow", "the share 5e-324/1e300 underflows to 0", available=[1e300, 5e-324, 1.0])
err(
    "overflow",
    "the ratio (1/3)/(1e-310/(2 + 1e-310)) is above the largest double",
    x=[1.0, 1.0, 1.0],
    available=[1.0, 1e-310, 1.0],
)

for c in cases:  # a value below the absolute tolerance needs a relative one, or 0 passes
    if "expected" in c and any(0 < abs(v) < TOL["abs"] for v in c["expected"]):
        c["tol"] = {"abs": 0.0, "rel": TOL["rel"]}

doc = {
    "schema": 1,
    "suite": "savage_selection_ratio",
    "description": "Savage's selection ratio (conventions: Savage's selection ratio; ADR 0606).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "savage_selection_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/savage_selection_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
