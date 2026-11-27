"""Writes vectors/cases/zenga_index.json, stdlib only.

The Zenga index (conventions: the Zenga index; ADR 0521): the defining mean of the gaps
between the mean of the n - k largest and the mean of the k smallest, over the former,
k < n, exactly in rationals.

Run from the repo root: python vectors/generators/zenga_index.py [--check]
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
    v = sorted(Fr(a) for a in x)
    n = len(v)
    q = Fr(0)
    for k in range(1, n):
        lo = sum(v[:k]) / k
        hi = sum(v[k:]) / (n - k)
        q += (hi - lo) / hi
    q /= n - 1
    cases.append(
        {
            "id": f"zenga_index.{cid}",
            "op": "zenga_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total: 1")
assert got == 1
got = add("two", [3.0, 1.0], "1 against 3: 2/3")
assert got == Fr(2, 3)
got = add("ramp", [4.0, 1.0, 3.0, 2.0], "ratios 1/3, 3/2 over 7/2, 2/4: 1 - (53/42)/3 = 73/126")
assert got == Fr(73, 126)
got = add("three", [3.0, 0.0, 1.0], "ratios 0, (1/2)/3: 1 - (1/6)/2 = 11/12")
assert got == Fr(11, 12)
got = add(
    "halves",
    [0.5, 0.25, 0.25, 1.0],
    "ratios (1/4)/(7/12), (1/4)/(3/4), (1/3)/1: 1 - (23/21)/3 = 40/63",
)
assert got == Fr(40, 63)
rng = random.Random(521)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(521).randint(0, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"zenga_index.{cid}",
            "op": "zenga_index",
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
    "suite": "zenga_index",
    "description": "The Zenga index (conventions: the Zenga index; ADR 0521).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "zenga_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/zenga_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
