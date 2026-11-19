"""Writes vectors/cases/aggregated_variance.json, stdlib only.

Aggregated variance (conventions: Aggregated variance; ADR 0355): the block means and their
population variance exact in rationals; then the least-squares slope of the logarithms and
1 + slope/2 in float.

Run from the repo root: python vectors/generators/aggregated_variance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def var(x, s):
    q = [Fr(v) for v in x]
    b = len(q) // s
    means = [sum(q[i * s:(i + 1) * s], Fr(0)) / s for i in range(b)]
    g = sum(means, Fr(0)) / b
    return sum(((u - g) ** 2 for u in means), Fr(0)) / b


def add(cid, x, sizes, why):
    exact = [var(x, s) for s in sizes]
    values = [float(v) for v in exact]
    lx = [math.log(s) for s in sizes]
    ly = [math.log(v) for v in exact]
    mx, my = math.fsum(lx) / len(lx), math.fsum(ly) / len(ly)
    beta = (math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
            / math.fsum((a - mx) ** 2 for a in lx))
    cases.append({"id": f"aggregated_variance.{cid}", "op": "aggregated_variance",
                  "args": {"samples": x, "sizes": sizes},
                  "expected": {"sizes": sizes, "values": values, "hurst": 1 + beta / 2},
                  "tol": TOL, "source": why})
    return exact, beta


exact, beta = add("pairs_by_hand", [1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0], [1, 2],
                  "+1, +1, -1, -1 repeated: at s = 1 and s = 2 the means are +-1, variance 1; "
                  "slope 0, so hurst 1")
assert exact == [1, 1] and beta == 0.0
exact, beta = add("odd_blocks", [1.0, -1.0] * 9, [1, 3, 9],
                  "+-1 alternating, 18 samples: s = 1 has variance 1; s = 3 means +-1/3, "
                  "variance 1/9; s = 9 means +-1/9, variance 1/81; slope -2, so hurst 0")
assert exact == [1, Fr(1, 9), Fr(1, 81)] and abs(beta + 2) < 1e-15
rng = random.Random(355)
add("noise", [rng.randint(-16, 16) / 8 for _ in range(128)], [1, 2, 4, 8, 16, 32],
    "128 random eighths from random.Random(355)")
add("leftover", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75,
                 0.0, 1.5, -0.75], [2, 3, 7], "fifteen arbitrary samples; s = 2 and s = 7 "
    "leave one over")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 3.0, -1.0, 0.25], "sizes": [1, 2]}
    base.update(args)
    cases.append({"id": f"aggregated_variance.{cid}", "op": "aggregated_variance",
                  "args": base, "error": "invalid_argument", "source": why})


err("one_size", "two sizes are needed", sizes=[2])
err("not_increasing", "sizes must be strictly increasing", sizes=[2, 2])
err("size_zero", "sizes must be at least 1", sizes=[0, 2])
err("one_block", "size 5 leaves one block of eight samples", sizes=[1, 5])
err("flat_means", "+-1 alternating at s = 2 has block means all 0",
    samples=[1.0, -1.0, 1.0, -1.0, 1.0, -1.0], sizes=[1, 2])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "aggregated_variance",
    "description": "Aggregated variance (conventions: Aggregated variance; ADR 0355).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "aggregated_variance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/aggregated_variance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
