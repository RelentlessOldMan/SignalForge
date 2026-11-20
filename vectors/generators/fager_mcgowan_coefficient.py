"""Writes vectors/cases/fager_mcgowan_coefficient.json, stdlib only.

The Fager-McGowan coefficient (conventions: Fager-McGowan coefficient; ADR 0438): the sets
counted directly, the roots taken in 40-digit decimals.

Run from the repo root: python vectors/generators/fager_mcgowan_coefficient.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    a = {i for i, v in enumerate(t) if v == 1}
    b = {i for i, v in enumerate(d) if v == 1}
    c = D(len(a & b)) / (D(len(a)) * D(len(b))).sqrt() - 1 / (2 * D(max(len(a), len(b))).sqrt())
    cases.append(
        {
            "id": f"fager_mcgowan_coefficient.{cid}",
            "op": "fager_mcgowan_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(c),
            "tol": TOL,
            "source": why,
        }
    )
    return c


def close(v, want):
    return abs(v - want) < D("1e-35")


got = add(
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "|A| = |B| = TP = 2: 1 - 1/(2 sqrt 2)"
)
assert close(got, 1 - 1 / (2 * D(2).sqrt()))
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    "|A| 3, |B| 1, TP 1: 1/sqrt 3 - 1/(2 sqrt 3) = 1/(2 sqrt 3)",
)
assert close(got, 1 / (2 * D(3).sqrt()))
got = add(
    "disjoint", [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], "|A| 2, |B| 1, TP 0: -1/(2 sqrt 2)"
)
assert close(got, -1 / (2 * D(2).sqrt()))
got = add(
    "partial",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0, 1.0],
    "A = {0, 1, 2}, B = {1, 2, 3, 4}: 2/sqrt 12 - 1/(2 sqrt 4) = 1/sqrt 3 - 1/4",
)
assert close(got, 1 / D(3).sqrt() - D(1) / 4)
got = add(
    "square",
    [1.0, 1.0, 1.0, 1.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0],
    "|A| 4, |B| 2, TP 2: 2/sqrt 8 - 1/(2 sqrt 4) = 1/sqrt 2 - 1/4",
)
assert close(got, 1 / D(2).sqrt() - D(1) / 4)
got = add("singles", [1.0, 0.0], [0.0, 1.0], "|A| = |B| = 1, TP 0: -1/2, the least value")
assert got == D(-1) / 2
rng = random.Random(438)
t = [float(rng.random() < 0.4) for _ in range(40)]
d = [float(rng.random() < 0.5) for _ in range(40)]
add("random", t, d, "40 items each from random.Random(438)")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"fager_mcgowan_coefficient.{cid}",
            "op": "fager_mcgowan_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_one", "the decision holds no 1", decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "fager_mcgowan_coefficient",
    "description": "The Fager-McGowan coefficient (conventions: Fager-McGowan coefficient;"
    " ADR 0438).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fager_mcgowan_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/fager_mcgowan_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
