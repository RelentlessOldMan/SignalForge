"""Writes vectors/cases/quintile_share_ratio.json, stdlib only.

The quintile share ratio (conventions: the quintile share ratio; ADR 0519): the Lorenz curve
of dyadic values, joined by straight lines, read at 1/5 and 4/5 exactly in rationals.

Run from the repo root: python vectors/generators/quintile_share_ratio.py [--check]
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
    q = (pts[-1] - at(pts, Fr(4, 5))) / at(pts, Fr(1, 5))
    cases.append(
        {
            "id": f"quintile_share_ratio.{cid}",
            "op": "quintile_share_ratio",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [1.0] * 5, "five equal values: 1")
assert got == 1
got = add("ramp_five", [5.0, 4.0, 3.0, 2.0, 1.0], "1 to 5: 5 over 1")
assert got == 5
got = add("ramp_ten", [float(k) for k in range(1, 11)], "1 to 10: (9 + 10) over (1 + 2)")
assert got == Fr(19, 3)
got = add(
    "three",
    [3.0, 1.0, 2.0],
    "n 3: low (3/5) 1 = 3/5; upto 1 + 2 + (2/5) 3 = 21/5, so (9/5)/(3/5) = 3",
)
assert got == 3
got = add("single", [5.0], "n 1: low (1/5) 5 = 1, upto (4/5) 5 = 4, so 1")
assert got == 1
got = add(
    "four", [4.0, 1.0, 3.0, 2.0], "n 4: low (4/5) 1; upto 6 + (1/5) 4 = 34/5, so (16/5)/(4/5) = 4"
)
assert got == 4
rng = random.Random(519)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(519).randint(1, 64)")
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
            "id": f"quintile_share_ratio.{cid}",
            "op": "quintile_share_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the smallest 20% must hold some of the total", samples=[0.0, 0.0, 0.0])
err("bottom_zero", "the smallest 20% hold nothing", samples=[0.0] * 2 + [1.0] * 8)

doc = {
    "schema": 1,
    "suite": "quintile_share_ratio",
    "description": "The quintile share ratio (conventions: the quintile share ratio; ADR 0519).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "quintile_share_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/quintile_share_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
