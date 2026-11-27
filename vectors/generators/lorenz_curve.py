"""Writes vectors/cases/lorenz_curve.json, stdlib only.

The Lorenz curve (conventions: the Lorenz curve; ADR 0517): dyadic values sorted and each
running share of the total formed exactly in rationals.

Run from the repo root: python vectors/generators/lorenz_curve.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = sorted(Fr(a) for a in x)
    total = sum(v)
    q = [Fr(0)]
    run = Fr(0)
    for a in v:
        run += a
        q.append(run / total)
    cases.append(
        {
            "id": f"lorenz_curve.{cid}",
            "op": "lorenz_curve",
            "args": {"samples": x},
            "expected": [float(a) for a in q],
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0], "every value equal: k/n")
assert got == [0, Fr(1, 3), Fr(2, 3), 1]
got = add("single", [5.0], "one value: 0 and 1")
assert got == [0, 1]
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total")
assert got == [0, 0, 0, 0, 1]
got = add("unsorted", [3.0, 0.0, 1.0], "sorted 0, 1, 3 of 4: 0, 0, 1/4, 1")
assert got == [0, 0, Fr(1, 4), 1]
got = add("ramp", [4.0, 1.0, 3.0, 2.0], "sorted 1, 2, 3, 4 of 10: 0, 1/10, 3/10, 6/10, 1")
assert got == [0, Fr(1, 10), Fr(3, 10), Fr(6, 10), 1]
got = add("halves", [0.5, 0.25, 0.25, 1.0], "sorted 1/4, 1/4, 1/2, 1 of 2: 0, 1/8, 1/4, 1/2, 1")
assert got == [0, Fr(1, 8), Fr(1, 4), Fr(1, 2), 1]
rng = random.Random(517)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(517).randint(0, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"lorenz_curve.{cid}",
            "op": "lorenz_curve",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "lorenz_curve",
    "description": "The Lorenz curve (conventions: the Lorenz curve; ADR 0517).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lorenz_curve.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lorenz_curve.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
