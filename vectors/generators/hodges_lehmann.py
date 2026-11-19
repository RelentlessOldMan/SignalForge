"""Writes vectors/cases/hodges_lehmann.json, stdlib only.

The Hodges-Lehmann shift estimate (conventions: Hodges-Lehmann shift estimate; ADR 0406): the
median of every pairwise difference, exact in rationals.

Run from the repo root: python vectors/generators/hodges_lehmann.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    d = sorted(Fr(u) - Fr(v) for u in x for v in y)
    m = len(d)
    hl = d[m // 2] if m % 2 else (d[m // 2 - 1] + d[m // 2]) / 2
    cases.append(
        {
            "id": f"hodges_lehmann.{cid}",
            "op": "hodges_lehmann",
            "args": {"x": x, "y": y},
            "expected": float(hl),
            "tol": TOL,
            "source": why,
        }
    )
    return hl


got = add("one_each", [4.0], [1.5], "one difference: 2.5")
assert got == Fr(5, 2)
got = add("odd", [1.0, 2.0, 10.0], [0.0], "differences 1, 2, 10: the median 2, unmoved by the 10")
assert got == 2
got = add("even", [1.0, 4.0], [0.0, 1.0], "differences 0, 1, 3, 4: (1 + 3)/2 = 2")
assert got == 2
got = add(
    "shift",
    [5.0, 6.0, 7.0],
    [1.0, 2.0, 3.0],
    "differences 2, 3, 3, 4, 4, 4, 5, 5, 6: the fifth is 4, the shift",
)
assert got == 4
got = add(
    "negative",
    [0.0, 0.5],
    [2.0, 3.0, 3.5],
    "differences -3.5, -3, -3, -2.5, -2, -1.5: (-3 - 2.5)/2 = -2.75",
)
assert got == Fr(-11, 4)
rng = random.Random(406)
x = [rng.gauss(0.7, 1.0) for _ in range(30)]
y = [rng.gauss(0.0, 1.0) for _ in range(45)]
add("gaussian", x, y, "30 and 45 values from random.Random(406), N(0.7, 1) and N(0, 1)")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hodges_lehmann.{cid}",
            "op": "hodges_lehmann",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_empty", "x needs a value", x=[])
err("y_empty", "y needs a value", y=[])
err("not_finite", "values must be finite", y=[1.0, "inf"])

doc = {
    "schema": 1,
    "suite": "hodges_lehmann",
    "description": "The Hodges-Lehmann shift estimate (conventions: Hodges-Lehmann shift "
    "estimate; ADR 0406).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hodges_lehmann.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hodges_lehmann.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
