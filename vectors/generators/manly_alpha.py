"""Writes vectors/cases/manly_alpha.json, stdlib only.

Manly's alpha (conventions: Manly's alpha; ADR 0602): the shares of each record and
(p/r)/sum(p/r) for each kind with fractions.

Run from the repo root: python vectors/generators/manly_alpha.py [--check]
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
    f = [wi / sum(w) for wi in w]
    v = [D(fi.numerator) / D(fi.denominator) for fi in f]
    cases.append(
        {
            "id": f"manly_alpha.{cid}",
            "op": "manly_alpha",
            "args": {"x": x, "available": available},
            "expected": [float(vi) + 0.0 for vi in v],
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert (
    add("as_available", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "use as availability: thirds")
    == [Fr(1, 3)] * 3
)
assert add(
    "even_use", [1.0, 1.0], [1.0, 3.0], "halves on 1/4, 3/4: ratios 2, 2/3, so 3/4, 1/4"
) == [Fr(3, 4), Fr(1, 4)]
assert add("one_kind_used", [1.0, 0.0], [1.0, 3.0], "only the first kind used: 1, 0") == [1, 0]
assert add(
    "uneven",
    [2.0, 1.0, 1.0],
    [1.0, 2.0, 1.0],
    "1/2, 1/4, 1/4 on 1/4, 1/2, 1/4: ratios 2, 1/2, 1, so 4/7, 1/7, 2/7",
) == [Fr(4, 7), Fr(1, 7), Fr(2, 7)]
assert add("one_kind", [2.0], [5.0], "one kind: 1") == [1]
assert (
    add(
        "huge",
        [1e308, 1e308],
        [1e308, 1e308],
        "the sums would overflow: halves on halves: 1/2, 1/2",
    )
    == [Fr(1, 2)] * 2
)
f = add(
    "tiny",
    [5e-324, 1.0],
    [1.0, 1.0],
    "the smallest double counts: 5e-324/(1 + 5e-324), 1/(1 + 5e-324)",
)
assert f == [Fr(5e-324) / (1 + Fr(5e-324)), 1 / (1 + Fr(5e-324))]
rng = random.Random(602)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
x[0] = 1.0
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    available,
    "x then available, 25 values each from random.Random(602)"
    ".choice([0, 0, 1, 2.5]) with x[0] = 1, and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"manly_alpha.{cid}",
            "op": "manly_alpha",
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
    "(1/3)/(1e-310/(2 + 1e-310)) is above the largest double",
    x=[1.0, 1.0, 1.0],
    available=[1.0, 1e-310, 1.0],
)

for c in cases:  # a value below the absolute tolerance needs a relative one, or 0 passes
    if "expected" in c and any(0 < abs(v) < TOL["abs"] for v in c["expected"]):
        c["tol"] = {"abs": 0.0, "rel": TOL["rel"]}

doc = {
    "schema": 1,
    "suite": "manly_alpha",
    "description": "Manly's alpha (conventions: Manly's alpha; ADR 0602).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "manly_alpha.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/manly_alpha.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
