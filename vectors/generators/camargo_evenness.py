"""Writes vectors/cases/camargo_evenness.json, stdlib only.

Camargo's evenness (conventions: Camargo's evenness; ADR 0533): the gaps between every
pair of shares of dyadic values, formed exactly in rationals.

Run from the repo root: python vectors/generators/camargo_evenness.py [--check]
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
    v = [Fr(a) for a in x]
    total = sum(v)
    sh = [a / total for a in v]
    n = len(sh)
    q = 1 - sum(abs(sh[i] - sh[j]) for i in range(n) for j in range(i + 1, n)) / n
    cases.append(
        {
            "id": f"camargo_evenness.{cid}",
            "op": "camargo_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "four equal shares, no gaps: 1") == 1
assert add("single", [5.0], "one value, no pairs: 1") == 1
assert add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "three gaps of 1: 1 - 3/4 = 1/4") == Fr(1, 4)
assert add("two", [3.0, 1.0], "shares 3/4, 1/4: 1 - (1/2)/2 = 3/4") == Fr(3, 4)
assert add(
    "ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 1, 3, 2 tenths, gaps summing to 1: 1 - 1/4 = 3/4"
) == Fr(3, 4)
assert add("three", [3.0, 0.0, 1.0], "gaps 3/4, 1/2, 1/4: 1 - (3/2)/3 = 1/2") == Fr(1, 2)
assert add(
    "halves",
    [0.5, 0.25, 0.25, 1.0],
    "shares 1/4, 1/8, 1/8, 1/2, gaps summing to 5/4: 1 - 5/16 = 11/16",
) == Fr(11, 16)
rng = random.Random(533)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(533).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"camargo_evenness.{cid}",
            "op": "camargo_evenness",
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
    "suite": "camargo_evenness",
    "description": "Camargo's evenness (conventions: Camargo's evenness; ADR 0533).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "camargo_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/camargo_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
