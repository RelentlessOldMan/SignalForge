"""Writes vectors/cases/wolfson_index.json, stdlib only.

The Wolfson polarization index (conventions: the Wolfson polarization index; ADR 0522): each
part from its own definition in rationals, the median from the middle values, L(1/2) by
reading the Lorenz points between k/n, and G from the pairwise sum of absolute differences.

Run from the repo root: python vectors/generators/wolfson_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def lorenz_at(v, p):
    """The Lorenz curve of the sorted values v, joined by straight lines, read at p."""
    n = len(v)
    total = sum(v)
    k = 0
    while Fr(k + 1, n) < p:
        k += 1
    lo = sum(v[:k])
    t = (p - Fr(k, n)) * n
    return (lo + t * v[k]) / total


def add(cid, x, why):
    v = sorted(Fr(a) for a in x)
    n = len(v)
    total = sum(v)
    mu = total / n
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    gini = sum(abs(a - b) for a in v for b in v) / (2 * n * total)
    q = 2 * (mu / med) * (1 - 2 * lorenz_at(v, Fr(1, 2)) - gini)
    cases.append(
        {
            "id": f"wolfson_index.{cid}",
            "op": "wolfson_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("single", [5.0], "one value: L(1/2) = 1/2, G = 0, so 0")
assert got == 0
got = add("two", [3.0, 1.0], "mean 2, median 2, L(1/2) 1/4, G 1/4: 2 (1 - 1/2 - 1/4) = 1/2")
assert got == Fr(1, 2)
got = add(
    "ramp", [4.0, 1.0, 3.0, 2.0], "mean = median 5/2, L(1/2) 3/10, G 1/4: 2 (1 - 3/5 - 1/4) = 3/10"
)
assert got == Fr(3, 10)
got = add(
    "three", [3.0, 0.0, 1.0], "mean 4/3, median 1, L(1/2) 1/8, G 1/2: 2 (4/3) (1 - 1/4 - 1/2) = 2/3"
)
assert got == Fr(2, 3)
got = add(
    "halves",
    [0.5, 0.25, 0.25, 1.0],
    "mean 1/2, median 3/8, L(1/2) 1/4, G 5/16: 2 (4/3) (3/16) = 1/2",
)
assert got == Fr(1, 2)
rng = random.Random(522)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(522).randint(1, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"wolfson_index.{cid}",
            "op": "wolfson_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the median must be above 0", samples=[0.0, 0.0, 0.0])
err("median_zero", "the median must be above 0", samples=[0.0, 0.0, 0.0, 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "wolfson_index",
    "description": "The Wolfson polarization index (conventions: the Wolfson polarization"
    " index; ADR 0522).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "wolfson_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/wolfson_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
