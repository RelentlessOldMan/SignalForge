"""Writes vectors/cases/strong_dominance.json, stdlib only.

Strong's dominance (conventions: Strong's dominance; ADR 0549): formed exactly in
rationals.

Run from the repo root: python vectors/generators/strong_dominance.py [--check]
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
    desc = sorted((a for a in v if a > 0), reverse=True)
    k = len(desc)
    q = max(sum(desc[:i]) / total - Fr(i, k) for i in range(1, k + 1))
    q = max(q, Fr(0))
    cases.append(
        {
            "id": f"strong_dominance.{cid}",
            "op": "strong_dominance",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "every share 1/4: 0") == 0
assert add("one_holds_all", [0.0, 4.0], "k = 1: 1 - 1 = 0") == 0
assert add("two", [3.0, 1.0], "3/4 - 1/2 = 1/4") == Fr(1, 4)
assert add("ramp3", [1.0, 2.0, 3.0], "1/2 - 1/3 = 5/6 - 2/3 = 1/6") == Fr(1, 6)
assert add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "5/9 - 1/4 = 11/36") == Fr(11, 36)
assert add("dominant", [10.0, 1.0, 1.0, 1.0, 1.0], "10/14 - 1/5 = 18/35") == Fr(18, 35)
assert add("ramp", [4.0, 1.0, 3.0, 2.0], "7/10 - 2/4 = 1/5") == Fr(1, 5)
assert add("halves", [0.5, 0.25, 0.25, 1.0], "1/2 - 1/4 = 3/4 - 2/4 = 1/4") == Fr(1, 4)
rng = random.Random(549)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(549).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"strong_dominance.{cid}",
            "op": "strong_dominance",
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
    "suite": "strong_dominance",
    "description": "Strong's dominance (conventions: Strong's dominance; ADR 0549).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "strong_dominance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/strong_dominance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
