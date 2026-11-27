"""Writes vectors/cases/palma_ratio.json, stdlib only.

The Palma ratio (conventions: the Palma ratio; ADR 0518): the Lorenz curve of dyadic values,
joined by straight lines, read at 2/5 and 9/10 exactly in rationals.

Run from the repo root: python vectors/generators/palma_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def at(points, p):
    """The curve through (k/n, points[k]) read at p, on the segment k/n <= p <= (k+1)/n."""
    n = len(points) - 1
    k = 0
    while Fr(k + 1, n) < p:
        k += 1
    t = (p - Fr(k, n)) * n
    return points[k] + t * (points[k + 1] - points[k])


def add(cid, x, why):
    v = sorted(Fr(a) for a in x)
    pts = [Fr(0)]
    for a in v:
        pts.append(pts[-1] + a)
    q = (pts[-1] - at(pts, Fr(9, 10))) / at(pts, Fr(2, 5))
    cases.append(
        {
            "id": f"palma_ratio.{cid}",
            "op": "palma_ratio",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [1.0] * 10, "ten equal values: 1 over 4")
assert got == Fr(1, 4)
got = add("ramp_ten", [float(k) for k in range(10, 0, -1)], "1 to 10: (10) over (1 + 2 + 3 + 4)")
assert got == 1
got = add(
    "ramp_five",
    [1.0, 2.0, 3.0, 4.0, 5.0],
    "n 5: low 1 + 2 = 3; upto 1 + 2 + 3 + 4 + 5/2 = 25/2, so (15 - 25/2)/3 = 5/6",
)
assert got == Fr(5, 6)
got = add(
    "three",
    [3.0, 1.0, 2.0],
    "n 3: low 1 + (1/5) 2 = 7/5; upto 1 + 2 + (7/10) 3 = 51/10, so (9/10)/(7/5) = 9/14",
)
assert got == Fr(9, 14)
got = add("single", [5.0], "n 1: low (2/5) 5 = 2, upto (9/10) 5, so (1/2)/2 = 1/4")
assert got == Fr(1, 4)
got = add(
    "four",
    [4.0, 1.0, 3.0, 2.0],
    "n 4: low 1 + (3/5) 2 = 11/5; upto 6 + (3/5) 4 = 42/5, so (8/5)/(11/5) = 8/11",
)
assert got == Fr(8, 11)
rng = random.Random(518)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(518).randint(1, 64)")
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
            "id": f"palma_ratio.{cid}",
            "op": "palma_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the smallest 40% must hold some of the total", samples=[0.0, 0.0, 0.0])
err("bottom_zero", "the smallest 40% hold nothing", samples=[0.0] * 4 + [1.0] * 6)

doc = {
    "schema": 1,
    "suite": "palma_ratio",
    "description": "The Palma ratio (conventions: the Palma ratio; ADR 0518).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "palma_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/palma_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
