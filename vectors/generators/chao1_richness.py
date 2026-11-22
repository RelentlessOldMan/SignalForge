"""Writes vectors/cases/chao1_richness.json, stdlib only.

The bias-corrected Chao1 richness (conventions: the Chao1 richness; ADR 0545): formed
exactly in rationals.

Run from the repo root: python vectors/generators/chao1_richness.py [--check]
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
    k = sum(1 for a in v if a > 0)
    f1 = sum(1 for a in v if a == 1)
    f2 = sum(1 for a in v if a == 2)
    q = k + Fr(f1 * (f1 - 1), 2 * (f2 + 1))
    cases.append(
        {
            "id": f"chao1_richness.{cid}",
            "op": "chao1_richness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("three_ones", [1.0, 1.0, 1.0, 2.0], "k = 4, F1 = 3, F2 = 1: 4 + 6/4") == Fr(11, 2)
assert add("no_ones", [2.0] * 3, "k = 3, F1 = 0: 3") == 3
assert add("two_ones", [1.0, 1.0], "k = 2, F1 = 2, F2 = 0: 2 + 2/2") == 3
assert add("single_one", [1.0], "k = 1, F1 = 1: 1") == 1
assert add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "k = 4, F1 = 2, F2 = 1: 4 + 2/4") == Fr(9, 2)
assert add("two", [3.0, 1.0], "k = 2, F1 = 1: 2") == 2
assert add("no_twos", [1.0, 1.0, 1.0, 1.0, 0.0, 3.0], "k = 5, F1 = 4, F2 = 0: 5 + 12/2") == 11
assert add("fractions", [0.5, 1.0, 2.5, 1.0], "k = 4, F1 = 2, F2 = 0: 4 + 1") == 5
rng = random.Random(545)
x = [float(rng.randint(0, 4)) for _ in range(30)]
add("random", x, "30 whole values from random.Random(545).randint(0, 4)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"chao1_richness.{cid}",
            "op": "chao1_richness",
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
    "suite": "chao1_richness",
    "description": "The Chao1 richness (conventions: the Chao1 richness; ADR 0545).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chao1_richness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chao1_richness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
