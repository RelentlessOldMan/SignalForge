"""Writes vectors/cases/bonferroni_index.json, stdlib only.

The Bonferroni index (conventions: the Bonferroni index; ADR 0520): the defining mean of the
gaps between the mean and the mean of the k smallest, k < n, exactly in rationals.

Run from the repo root: python vectors/generators/bonferroni_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, why):
    v = sorted(Fr(a) for a in x)
    n = len(v)
    mu = sum(v) / n
    q = sum((mu - sum(v[:k]) / k) / mu for k in range(1, n)) / (n - 1)
    cases.append(
        {
            "id": f"bonferroni_index.{cid}",
            "op": "bonferroni_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total: 1")
assert got == 1
got = add("two", [3.0, 1.0], "mean 2, m1 1: (1/2)")
assert got == Fr(1, 2)
got = add("ramp", [4.0, 1.0, 3.0, 2.0], "mean 5/2, m 1, 3/2, 2: (3/2 + 1 + 1/2)/(5/2)/3 = 2/5")
assert got == Fr(2, 5)
got = add("three", [3.0, 0.0, 1.0], "mean 4/3, m 0, 1/2: (1 + 5/8)/2 = 13/16")
assert got == Fr(13, 16)
got = add("halves", [0.5, 0.25, 0.25, 1.0], "mean 1/2, m 1/4, 1/4, 1/3: (1/2 + 1/2 + 1/3)/3 = 4/9")
assert got == Fr(4, 9)
rng = random.Random(520)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(520).randint(0, 64)")
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
            "id": f"bonferroni_index.{cid}",
            "op": "bonferroni_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs at least 2 values", samples=[])
err("single", "the record needs at least 2 values", samples=[5.0])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "bonferroni_index",
    "description": "The Bonferroni index (conventions: the Bonferroni index; ADR 0520).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bonferroni_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bonferroni_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
