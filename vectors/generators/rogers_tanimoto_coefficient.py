"""Writes vectors/cases/rogers_tanimoto_coefficient.json, stdlib only.

The Rogers-Tanimoto coefficient (conventions: Rogers-Tanimoto coefficient; ADR 0425): the
agreements counted directly.

Run from the repo root: python vectors/generators/rogers_tanimoto_coefficient.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    m = sum(1 for a, b in zip(t, d) if a == b)
    v = Fr(m, m + 2 * (len(t) - m))
    cases.append(
        {
            "id": f"rogers_tanimoto_coefficient.{cid}",
            "op": "rogers_tanimoto_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "the same record: 1")
assert got == 1
got = add("all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "shared absences count: 1")
assert got == 1
got = add("opposite", [1.0, 0.0, 1.0], [0.0, 1.0, 0.0], "every item differs: 0")
assert got == 0
got = add(
    "partial",
    [1.0, 1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0, 1.0],
    "agree at items 0, 2, 4, differ at 1, 3: 3/(3 + 4) = 3/7",
)
assert got == Fr(3, 7)
rng = random.Random(425)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.8 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(425), about a fifth flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"rogers_tanimoto_coefficient.{cid}",
            "op": "rogers_tanimoto_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", truth=[1.0, 2.0, 0.0])

doc = {
    "schema": 1,
    "suite": "rogers_tanimoto_coefficient",
    "description": "The Rogers-Tanimoto coefficient (conventions: Rogers-Tanimoto coefficient;"
    " ADR 0425).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rogers_tanimoto_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/rogers_tanimoto_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
