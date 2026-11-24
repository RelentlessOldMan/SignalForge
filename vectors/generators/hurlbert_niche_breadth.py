"""Writes vectors/cases/hurlbert_niche_breadth.json, stdlib only.

Hurlbert's niche breadth (conventions: Hurlbert's niche breadth; ADR 0601): the shares
of each record, 1 / sum p^2 / r and (B' - r_min)/(1 - r_min) with fractions.

Run from the repo root: python vectors/generators/hurlbert_niche_breadth.py [--check]
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


def add(cid, x, available, why, standardized=False):
    xs = [Fr(a) for a in x]
    avs = [Fr(c) for c in available]
    sx = sum(xs)
    sa = sum(avs)
    f = 1 / sum((a / sx) ** 2 / (c / sa) for a, c in zip(xs, avs))
    args = {"x": x, "available": available}
    if standardized:
        least = min(c / sa for c in avs)
        f = (f - least) / (1 - least)
        args["standardized"] = True
    v = D(f.numerator) / D(f.denominator)
    cases.append(
        {
            "id": f"hurlbert_niche_breadth.{cid}",
            "op": "hurlbert_niche_breadth",
            "args": args,
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert (
    add("as_available", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "use as availability: 1 / sum p = 1") == 1
)
assert (
    add(
        "as_available_std",
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
        "use as availability, standardized: (1 - 1/6)/(1 - 1/6) = 1",
        True,
    )
    == 1
)
assert add("even_use", [1.0, 1.0], [1.0, 3.0], "halves on 1/4, 3/4: 1/(1 + 1/3) = 3/4") == D(3) / 4
assert (
    add(
        "even_use_std",
        [1.0, 1.0],
        [1.0, 3.0],
        "halves on 1/4, 3/4, standardized: (3/4 - 1/4)/(3/4) = 2/3",
        True,
    )
    == D(2) / 3
)
assert add("scarcest", [1.0, 0.0], [1.0, 3.0], "all on the kind with share 1/4: 1/4") == D(1) / 4
assert (
    add("scarcest_std", [1.0, 0.0], [1.0, 3.0], "all on the scarcest kind, standardized: 0", True)
    == 0
)
assert add("commonest", [0.0, 1.0], [1.0, 3.0], "all on the kind with share 3/4: 3/4") == D(3) / 4
assert (
    add(
        "uneven",
        [2.0, 1.0, 1.0],
        [1.0, 2.0, 1.0],
        "1/2, 1/4, 1/4 on 1/4, 1/2, 1/4: 1/(1 + 1/8 + 1/4) = 8/11",
    )
    == D(8) / 11
)
assert (
    add(
        "uneven_std",
        [2.0, 1.0, 1.0],
        [1.0, 2.0, 1.0],
        "standardized: (8/11 - 1/4)/(3/4) = 7/11",
        True,
    )
    == D(7) / 11
)
assert add("one_kind", [2.0], [5.0], "one kind: 1") == 1
assert (
    add("huge", [1e308, 1e308], [1e308, 1e308], "the sums would overflow: halves on halves: 1") == 1
)
assert near(
    add(
        "tiny",
        [5e-324, 1.0],
        [1.0, 1.0],
        "the smallest double counts: 1/(2 (1 + 2.5e-647)/(1 + 5e-324)^2), 1/2 to double precision",
    ),
    D(1) / 2,
)
rng = random.Random(601)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
x[0] = 1.0
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    available,
    "x then available, 25 values each from random.Random(601)"
    ".choice([0, 0, 1, 2.5]) with x[0] = 1, and .choice([0.5, 1, 2.5])",
)
add("random_std", x, available, "the random case, standardized", True)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hurlbert_niche_breadth.{cid}",
            "op": "hurlbert_niche_breadth",
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
    "(1/3)^2/(1e-310/(2 + 1e-310)) is above the largest double",
    x=[1.0, 1.0, 1.0],
    available=[1.0, 1e-310, 1.0],
)
err(
    "one_kind_std",
    "the standardized form needs at least two kinds",
    x=[2.0],
    available=[5.0],
    standardized=True,
)

doc = {
    "schema": 1,
    "suite": "hurlbert_niche_breadth",
    "description": "Hurlbert's niche breadth (conventions: Hurlbert's niche breadth; ADR 0601).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hurlbert_niche_breadth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hurlbert_niche_breadth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
