"""Writes vectors/cases/ace_richness.json, stdlib only.

The ACE richness (conventions: the ACE richness; ADR 0551): formed exactly in rationals
from the counts F_i of each value.

Run from the repo root: python vectors/generators/ace_richness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    f = {i: sum(1 for a in v if a == i) for i in range(1, 11)}
    s_abund = sum(1 for a in v if a > 10)
    s_rare = sum(f.values())
    if s_rare == 0:
        q = Fr(s_abund)
    else:
        n_rare = sum(i * f[i] for i in f)
        c = 1 - Fr(f[1], n_rare)
        g = max(
            Fr(s_rare) / c * sum(i * (i - 1) * f[i] for i in f) / (n_rare * (n_rare - 1)) - 1, Fr(0)
        )
        q = s_abund + s_rare / c + f[1] / c * g
    cases.append(
        {
            "id": f"ace_richness.{cid}",
            "op": "ace_richness",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("abundant_only", [20.0, 15.0, 0.0], "no rare kinds: S_abund = 2") == 2
assert add("no_singletons", [2.0, 3.0], "C = 1, gamma^2 = max(16/20 - 1, 0) = 0: 2") == 2
assert add("one_singleton", [1.0, 2.0], "C = 2/3, gamma^2 = max(1 - 1, 0) = 0: 3") == 3
assert add("three_singletons", [1.0, 1.0, 1.0, 2.0], "C = 2/5, gamma^2 = 0: 4/(2/5)") == 10
assert add("mixed", [1.0, 1.0, 2.0, 3.0, 20.0], "C = 5/7, gamma^2 = 1/15: 1 + 28/5 + 14/75") == (
    Fr(509, 75)
)
assert add("cut_off", [1.0, 1.0, 10.0, 0.0, 5.0], "10 is rare: C = 15/17, gamma^2 = 5/6") == (
    Fr(289, 45)
)
assert add("eleven", [11.0, 2.0, 1.0], "11 is abundant: 1 + 3") == 4
rng = random.Random(551)
x = [float(rng.randint(0, 14)) for _ in range(40)]
add("random", x, "40 whole values from random.Random(551).randint(0, 14)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"ace_richness.{cid}",
            "op": "ace_richness",
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
err("all_singletons", "the rare values must not all be 1", samples=[1.0, 1.0])
err("abundant_and_one", "the rare values must not all be 1", samples=[30.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "ace_richness",
    "description": "The ACE richness (conventions: the ACE richness; ADR 0551).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ace_richness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ace_richness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
