"""Writes vectors/cases/bonachela_entropy.json, stdlib only.

The Bonachela entropy (conventions: the Bonachela entropy; ADR 0560): each inner range
summed directly in exact rationals.

Run from the repo root: python vectors/generators/bonachela_entropy.py [--check]
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
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    q = Fr(0)
    for a in v:
        if a > 0:
            q += (a + 1) * sum((Fr(1, j) for j in range(a + 2, total + 3)), Fr(0))
    q /= total + 2
    cases.append(
        {
            "id": f"bonachela_entropy.{cid}",
            "op": "bonachela_entropy",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("two_ones", [1.0, 1.0], "(1/4) 2 (2)(1/3 + 1/4) = 7/12") == Fr(7, 12)
assert add("two_twos", [2.0, 2.0], "(1/6) 2 (3)(1/4 + 1/5 + 1/6) = 37/60") == Fr(37, 60)
assert add("one_kind", [0.0, 4.0], "(1/6) 5 (1/6) = 5/36") == Fr(5, 36)
assert add("single", [1.0], "(1/3) 2 (1/3) = 2/9") == Fr(2, 9)
add("ramp", [1.0, 2.0, 3.0], "N = 6")
add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9")
add("large", [100.0, 200.0, 300.0, 400.0], "N = 1000")
rng = random.Random(560)
x = [float(rng.randint(0, 9)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(560).randint(0, 9)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"bonachela_entropy.{cid}",
            "op": "bonachela_entropy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000 000", samples=[10000000.0, 1.0])

doc = {
    "schema": 1,
    "suite": "bonachela_entropy",
    "description": "The Bonachela entropy (conventions: the Bonachela entropy; ADR 0560).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bonachela_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bonachela_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
