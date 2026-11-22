"""Writes vectors/cases/hurlbert_pie.json, stdlib only.

Hurlbert's PIE (conventions: Hurlbert's PIE; ADR 0548): formed exactly in rationals.

Run from the repo root: python vectors/generators/hurlbert_pie.py [--check]
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
    q = total / (total - 1) * (1 - sum((a / total) ** 2 for a in v))
    cases.append(
        {
            "id": f"hurlbert_pie.{cid}",
            "op": "hurlbert_pie",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("two_ones", [1.0, 1.0], "N = 2: 2 (1 - 1/2) = 1") == 1
assert add("two_twos", [2.0, 2.0], "N = 4: (4/3)(1/2) = 2/3") == Fr(2, 3)
assert add("one_holds_all", [0.0, 4.0], "one kind: 0") == 0
assert add("two", [3.0, 1.0], "N = 4: (4/3)(6/16) = 1/2") == Fr(1, 2)
assert add("ramp", [1.0, 2.0, 3.0], "N = 6: (6/5)(22/36) = 11/15") == Fr(11, 15)
assert add("four_ones", [1.0] * 4, "N = 4: (4/3)(3/4) = 1") == 1
assert add("halves", [0.5, 0.25, 0.25, 1.0], "N = 2: 2 (42/64) = 21/16, above 1") == (Fr(21, 16))
rng = random.Random(548)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(548).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hurlbert_pie.{cid}",
            "op": "hurlbert_pie",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be above 1", samples=[0.0, 0.0, 0.0])
err("total_one", "the total must be above 1", samples=[0.5, 0.5])
err("single_one", "the total must be above 1", samples=[1.0])

doc = {
    "schema": 1,
    "suite": "hurlbert_pie",
    "description": "Hurlbert's PIE (conventions: Hurlbert's PIE; ADR 0548).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hurlbert_pie.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hurlbert_pie.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
