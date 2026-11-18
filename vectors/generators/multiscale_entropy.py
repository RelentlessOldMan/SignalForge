"""Writes vectors/cases/multiscale_entropy.json, stdlib only.

Multiscale entropy (conventions: Multiscale entropy; ADR 0338): for each scale the means of
non-overlapping windows (exact window sums of small dyadic samples, one rounded division, as
float does it), then sample entropy -ln(A/B) with the match counts taken exactly in rationals.
Every comparison with r is asserted to agree with float, so rounding cannot flip a match.

Run from the repo root: python vectors/generators/multiscale_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def near(a, b, r):
    exact = abs(Fr(a) - Fr(b)) <= Fr(r)
    assert exact == (abs(a - b) <= r), (a, b, r)
    return exact


def sampen(y, m, r):
    starts = len(y) - m
    b = a = 0
    for i in range(starts - 1):
        for j in range(i + 1, starts):
            if all(near(y[i + k], y[j + k], r) for k in range(m)):
                b += 1
                if near(y[i + m], y[j + m], r):
                    a += 1
    assert b > 0
    return "inf" if a == 0 else -math.log(Fr(a, b))


def mse(x, m, r, scales):
    out = []
    for s in scales:
        coarse = [float(Fr(sum(Fr(v) for v in x[j * s:(j + 1) * s])) / s)
                  for j in range(len(x) // s)]
        out.append(sampen(coarse, m, r))
    return out


def add(cid, x, m, r, scales, why):
    e = mse(x, m, r, scales)
    cases.append({"id": f"multiscale_entropy.{cid}", "op": "multiscale_entropy",
                  "args": {"samples": x, "m": m, "r": r, "scales": scales}, "expected": e,
                  "tol": TOL, "source": why})
    return e


e = add("alternating", [1.0, -1.0] * 12, 1, 0.5, [1, 2], "+-1 alternating: scale 1 matches "
        "every same-phase pair for m and m + 1 (0); scale 2 is all zeros (0)")
assert e == [0.0, 0.0], e
rng = random.Random(338)
noise = [rng.randint(-8, 8) / 4 for _ in range(90)]
add("noise", noise, 2, 0.625, [1, 2, 3, 5], "90 random quarter-integers from "
    "random.Random(338), r = 0.625")
add("order", noise, 1, 0.5, [4, 1], "the same samples, m = 1, scales out of order")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0], "m": 1, "r": 0.5,
            "scales": [1]}
    base.update(args)
    cases.append({"id": f"multiscale_entropy.{cid}", "op": "multiscale_entropy",
                  "args": base, "error": "invalid_argument", "source": why})


err("scale_zero", "each scale must be at least 1", scales=[0])
err("scale_too_big", "floor(N / scale) must be at least m + 2", scales=[3])
err("no_scales", "scales must not be empty", scales=[])
err("no_matches", "no pair matches for m at scale 1", samples=[0.0, 4.0, 8.0, 12.0, 16.0],
    r=1.0)
err("r_negative", "r must be at least 0", r=-1.0)

doc = {
    "schema": 1,
    "suite": "multiscale_entropy",
    "description": "Multiscale entropy (conventions: Multiscale entropy; ADR 0338).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "multiscale_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/multiscale_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
