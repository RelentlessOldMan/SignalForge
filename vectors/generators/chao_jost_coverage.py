"""Writes vectors/cases/chao_jost_coverage.json, stdlib only.

The Chao-Jost coverage (conventions: the Chao-Jost coverage; ADR 0553): formed exactly in
rationals.

Run from the repo root: python vectors/generators/chao_jost_coverage.py [--check]
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
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    f1 = sum(1 for a in v if a == 1)
    f2 = sum(1 for a in v if a == 2)
    q = Fr(1) if f1 == 0 else 1 - Fr(f1, total) * Fr((total - 1) * f1, (total - 1) * f1 + 2 * f2)
    cases.append(
        {
            "id": f"chao_jost_coverage.{cid}",
            "op": "chao_jost_coverage",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("no_singletons", [2.0, 2.0, 0.0, 5.0], "F1 = 0: 1") == 1
assert add("no_doubletons", [3.0, 1.0], "F2 = 0: Good's 1 - 1/4") == Fr(3, 4)
assert add("all_singletons", [1.0, 1.0], "N = 2, F1 = 2: 1 - 1 = 0") == 0
assert add("one_each", [1.0, 2.0], "N = 3: 1 - (1/3)(2/4) = 5/6") == Fr(5, 6)
assert add("ramp", [1.0, 1.0, 2.0, 3.0], "N = 7: 1 - (2/7)(12/14) = 37/49") == Fr(37, 49)
assert add("mixed", [5.0, 1.0, 1.0, 0.0, 2.0], "N = 9: 1 - (2/9)(16/18) = 65/81") == (Fr(65, 81))
assert add(
    "many_twos", [1.0, 2.0, 2.0, 2.0, 2.0, 10.0], "N = 19: 1 - (1/19)(18/26) = 238/247"
) == Fr(238, 247)
rng = random.Random(553)
x = [float(rng.randint(0, 4)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(553).randint(0, 4)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"chao_jost_coverage.{cid}",
            "op": "chao_jost_coverage",
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
err("total_one", "the total must be above 1", samples=[0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "chao_jost_coverage",
    "description": "The Chao-Jost coverage (conventions: the Chao-Jost coverage; ADR 0553).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chao_jost_coverage.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chao_jost_coverage.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
