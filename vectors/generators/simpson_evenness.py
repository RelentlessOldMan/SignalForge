"""Writes vectors/cases/simpson_evenness.json, stdlib only.

Simpson's evenness (conventions: Simpson's evenness; ADR 0532): one over n times the
squared shares of dyadic values, formed exactly in rationals.

Run from the repo root: python vectors/generators/simpson_evenness.py [--check]
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
    v = [Fr(a) for a in x]
    total = sum(v)
    q = 1 / (len(v) * sum((a / total) ** 2 for a in v))
    cases.append(
        {
            "id": f"simpson_evenness.{cid}",
            "op": "simpson_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "four equal shares: 1/(4 (4/16)) = 1") == 1
assert add("single", [5.0], "one value: 1") == 1
assert add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one share of 1: 1/4") == Fr(1, 4)
assert add("two", [3.0, 1.0], "shares 3/4, 1/4: 1/(2 (10/16)) = 4/5") == Fr(4, 5)
assert add("ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 1, 3, 2 tenths: 1/(4 (30/100)) = 5/6") == (
    Fr(5, 6)
)
assert add("three", [3.0, 0.0, 1.0], "shares 3/4, 0, 1/4: 1/(3 (10/16)) = 8/15") == Fr(8, 15)
assert add(
    "halves", [0.5, 0.25, 0.25, 1.0], "shares 1/4, 1/8, 1/8, 1/2: 1/(4 (22/64)) = 8/11"
) == Fr(8, 11)
rng = random.Random(532)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(532).randint(0, 64)")
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
            "id": f"simpson_evenness.{cid}",
            "op": "simpson_evenness",
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
    "suite": "simpson_evenness",
    "description": "Simpson's evenness (conventions: Simpson's evenness; ADR 0532).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "simpson_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/simpson_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
