"""Writes vectors/cases/generalized_entropy_index.json, stdlib only.

The generalized entropy index (conventions: the generalized entropy index; ADR 0516): each
ratio of a dyadic value to the mean exact in rationals, each power exp(alpha ln r) in
40-digit decimals.

Run from the repo root: python vectors/generators/generalized_entropy_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as Fr

getcontext().prec = 40

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, alpha, why):
    v = [Fr(a) for a in x]
    n = len(v)
    mean = sum(v) / n
    rs = [dec(a / mean) for a in v]
    if alpha == 0:
        q = -sum(r.ln() for r in rs) / n
    elif alpha == 1:
        q = sum(r * r.ln() for r in rs) / n
    else:
        al = dec(Fr(alpha))
        q = sum((al * r.ln()).exp() - 1 for r in rs) / n / (al * (al - 1))
    cases.append(
        {
            "id": f"generalized_entropy_index.{cid}",
            "op": "generalized_entropy_index",
            "args": {"samples": x, "alpha": alpha},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("equal", [2.0, 2.0, 2.0], 2.0, "every value equal: 0")
assert close(got, 0)
got = add("half_cv_squared", [1.0, 3.0], 2.0, "half the squared CV, (1/2)^2/2 = 1/8")
assert close(got, D(1) / 8)
got = add("mld", [1.0, 3.0], 0.0, "the mean log deviation: (2 ln 2 - ln 3)/2")
assert close(got, (2 * D(2).ln() - D(3).ln()) / 2)
got = add("theil", [1.0, 3.0], 1.0, "the Theil index: (3/2 ln(3/2) - 1/2 ln 2)/2")
assert close(got, (D(3) / 2 * (D(3) / 2).ln() - D(2).ln() / 2) / 2)
got = add("minus_one", [1.0, 3.0], -1.0, "(1/(2 2))(2/1 + 2/3 - 2) = 1/6")
assert close(got, D(1) / 6)
got = add(
    "half", [1.0, 4.0], 0.5, "ratios 2/5, 8/5: (1/(2 (-1/4)))(3 sqrt(2/5) - 2) = 4 - 6 sqrt(2/5)"
)
assert close(got, 4 - 6 * (D(2) / 5).sqrt())
got = add(
    "three",
    [1.0, 2.0, 4.0],
    3.0,
    "mean 7/3: (1/(3 6))((27/343)(1 + 8 + 64) - 3) = (1971/343 - 3)/18 = 157/1029",
)
assert close(got, D(157) / 1029)
rng = random.Random(516)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, 1.5, "30 values k/8, k from random.Random(516).randint(1, 64); alpha 3/2")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "alpha": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"generalized_entropy_index.{cid}",
            "op": "generalized_entropy_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("zero", "values must be greater than 0", samples=[1.0, 0.0, 2.0])
err("negative", "values must be greater than 0", samples=[1.0, -0.5, 2.0])

doc = {
    "schema": 1,
    "suite": "generalized_entropy_index",
    "description": "The generalized entropy index (conventions: the generalized entropy"
    " index; ADR 0516).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "generalized_entropy_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/generalized_entropy_index.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
