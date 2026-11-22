"""Writes vectors/cases/bulla_evenness.json, stdlib only.

Bulla's evenness (conventions: Bulla's evenness; ADR 0535): the overlap of the shares of
dyadic values with equal shares, rescaled, formed exactly in rationals.

Run from the repo root: python vectors/generators/bulla_evenness.py [--check]
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
    even = Fr(1, len(v))
    o = sum(min(a / total, even) for a in v)
    q = (o - even) / (1 - even)
    cases.append(
        {
            "id": f"bulla_evenness.{cid}",
            "op": "bulla_evenness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "four equal shares, overlap 1: 1") == 1
assert add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "overlap 1/4: 0") == 0
assert add("two", [3.0, 1.0], "overlap 1/2 + 1/4 = 3/4: (1/4)/(1/2) = 1/2") == Fr(1, 2)
assert add(
    "ramp", [4.0, 1.0, 3.0, 2.0], "overlap 1/4 + 1/10 + 1/4 + 1/5 = 4/5: (11/20)/(3/4) = 11/15"
) == Fr(11, 15)
assert add("three", [3.0, 0.0, 1.0], "overlap 1/3 + 0 + 1/4 = 7/12: (1/4)/(2/3) = 3/8") == Fr(3, 8)
assert add(
    "halves", [0.5, 0.25, 0.25, 1.0], "overlap 1/4 + 1/8 + 1/8 + 1/4 = 3/4: (1/2)/(3/4) = 2/3"
) == Fr(2, 3)
assert add("one_zero", [0.0, 2.0, 2.0, 2.0, 2.0], "overlap 4/5: (3/5)/(4/5) = 3/4") == Fr(3, 4)
rng = random.Random(535)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(535).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"bulla_evenness.{cid}",
            "op": "bulla_evenness",
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
    "suite": "bulla_evenness",
    "description": "Bulla's evenness (conventions: Bulla's evenness; ADR 0535).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bulla_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bulla_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
