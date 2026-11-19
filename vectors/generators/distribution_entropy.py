"""Writes vectors/cases/distribution_entropy.json, stdlib only.

Distribution entropy (conventions: Distribution entropy; ADR 0348): the Chebyshev distances of
all window pairs of dyadic samples and each bin min(M - 1, floor((d - lo) M / (hi - lo)))
exact in rationals, asserting no bin position below M is within 1e-9 of an integer unless it
is exactly one; exact counts, then -sum p ln p / ln M in float.

Run from the repo root: python vectors/generators/distribution_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, m, bins, why):
    q = [Fr(v) for v in x]
    windows = len(q) - m + 1
    d = [max(abs(q[j + l] - q[i + l]) for l in range(m))
         for i in range(windows - 1) for j in range(i + 1, windows)]
    lo, hi = min(d), max(d)
    if hi == lo:
        v = 0.0
    else:
        b = []
        for u in d:
            t = (u - lo) * bins / (hi - lo)
            if t < bins and t.denominator != 1:
                assert abs(float(t) - round(float(t))) > 1e-9, t
            b.append(min(bins - 1, math.floor(t)))
        n = len(b)
        v = -math.fsum(c / n * math.log(c / n) for c in Counter(b).values()) / math.log(bins)
    args = {"samples": x, "m": m}
    if bins != 512:
        args["bins"] = bins
    cases.append({"id": f"distribution_entropy.{cid}", "op": "distribution_entropy",
                  "args": args, "expected": v, "tol": TOL, "source": why})
    return d, v


d, v = add("equal_distances", [0.0, 1.0, 2.0], 1, 4, "three points 0, 1, 2: distances 1, 2, 1 "
           "fall in bins 0, 3, 0")
assert sorted(d) == [1, 1, 2]
assert abs(v - -(2 / 3 * math.log(2 / 3) + 1 / 3 * math.log(1 / 3)) / math.log(4)) < 1e-15
d, v = add("one_distance", [0.0, 1.0, 0.0, 1.0], 3, 8, "two windows: one pair, one bin, so 0")
assert v == 0.0
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0], 2, 10, "eighteen arbitrary dyadic samples, M = 10")
rng = random.Random(348)
add("noise_default_bins", [rng.randint(-40, 40) / 8 for _ in range(150)], 3, 512,
    "150 random eighths from random.Random(348), m = 3, the default 512 bins")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2}
    base.update(args)
    cases.append({"id": f"distribution_entropy.{cid}", "op": "distribution_entropy",
                  "args": base, "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("one_bin", "bins must be at least 2", bins=1)
err("too_short", "one window has no pair", m=5)
err("inf", "samples must be finite", samples=[0.0, "inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "distribution_entropy",
    "description": "Distribution entropy (conventions: Distribution entropy; ADR 0348).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "distribution_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/distribution_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
