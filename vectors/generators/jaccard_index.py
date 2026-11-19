"""Writes vectors/cases/jaccard_index.json, stdlib only.

The Jaccard index (conventions: Jaccard index; ADR 0388): intersection and union counted as
sets of indices.

Run from the repo root: python vectors/generators/jaccard_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, truth, decision, why):
    a = {i for i, v in enumerate(truth) if v == 1}
    b = {i for i, v in enumerate(decision) if v == 1}
    j = Fr(len(a & b), len(a | b))
    cases.append(
        {
            "id": f"jaccard_index.{cid}",
            "op": "jaccard_index",
            "args": {"truth": truth, "decision": decision},
            "expected": float(j),
            "tol": TOL,
            "source": why,
        }
    )
    return j


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "the same set: J = 1")
assert got == 1
got = add("disjoint", [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], "no overlap: J = 0")
assert got == 0
got = add(
    "overlap",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 1.0],
    "{0, 1, 2} and {0, 1, 3, 4}: intersection 2, union 5, J = 2/5 (F1 = 4/7 = 2J/(1 + J))",
)
assert got == Fr(2, 5)
rng = random.Random(388)
truth = [1.0 if rng.random() < 0.25 else 0.0 for _ in range(200)]
decision = [t if rng.random() < 0.85 else 1.0 - t for t in truth]
add(
    "noisy_mask",
    truth,
    decision,
    "200 items from random.Random(388), 25% marked, each decision flipped with probability 0.15",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0, 0.0], "decision": [1.0, 0.0, 0.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"jaccard_index.{cid}",
            "op": "jaccard_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.0, 3.0, 0.0])
err(
    "empty_union",
    "the union is empty when neither record has a 1",
    truth=[0.0, 0.0, 0.0, 0.0],
    decision=[0.0, 0.0, 0.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "jaccard_index",
    "description": "The Jaccard index (conventions: Jaccard index; ADR 0388).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "jaccard_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/jaccard_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
