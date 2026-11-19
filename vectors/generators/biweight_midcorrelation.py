"""Writes vectors/cases/biweight_midcorrelation.json, stdlib only.

Biweight midcorrelation (conventions: Biweight midcorrelation; ADR 0373): dyadic samples,
the medians, MADs, weights and sums exact in rationals, then the square root and the
quotient in float.

Run from the repo root: python vectors/generators/biweight_midcorrelation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def median(v):
    s = sorted(v)
    k = len(s)
    return s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2


def terms(v):
    q = [Fr(u) for u in v]
    m = median(q)
    d = [u - m for u in q]
    mad = median([abs(u) for u in d])
    assert mad > 0
    out = []
    for u in d:
        r = u / (9 * mad)
        assert abs(abs(float(r)) - 1) > 1e-9
        out.append(u * (1 - r * r) ** 2 if abs(r) < 1 else Fr(0))
    return out


def add(cid, x, y, why):
    p, q = terms(x), terms(y)
    pq = sum((a * b for a, b in zip(p, q)), Fr(0))
    pp = sum((a * a for a in p), Fr(0))
    qq = sum((b * b for b in q), Fr(0))
    v = float(pq) / math.sqrt(float(pp) * float(qq))
    cases.append({"id": f"biweight_midcorrelation.{cid}", "op": "biweight_midcorrelation",
                  "args": {"x": x, "y": y}, "expected": v, "tol": TOL, "source": why})
    return p, q, v


p, q, v = add("line", [1.0, 2.0, 3.0, 4.0, 5.0], [3.0, 5.0, 7.0, 9.0, 11.0],
              "y = 2x + 1: the weighted deviations of y are twice those of x, so 1")
assert all(b == 2 * a for a, b in zip(p, q)) and v == 1.0
p, q, v = add("outlier_cut_off", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0],
              [1.0, 2.0, 3.0, 4.0, 5.0, 200.0],
              "both medians 7/2, MADs 3/2: the 100 and the 200 are more than 13.5 from "
              "the median, so their weights are 0, and the rest agree exactly: 1")
assert p[-1] == 0 and q[-1] == 0 and v == 1.0
p, q, v = add("by_hand", [-1.0, 0.0, 1.0], [0.0, 1.0, -1.0],
              "x: median 0, MAD 1, u = -1/9, 0, 1/9, w = (80/81)^2; y: median 0, MAD 1, "
              "a for x = -w, 0, w and for y = 0, w, -w: sum ab = -w^2, both sums of "
              "squares 2w^2: -1/2")
assert v == -0.5
rng = random.Random(373)
xs = [rng.randint(-32, 32) / 8 for _ in range(50)]
ys = [v + rng.randint(-16, 16) / 8 for v in xs]
xs[7], ys[7] = 60.0, -60.0
add("noisy_pair_with_outlier", xs, ys,
    "50 random eighths from random.Random(373), y = x plus more, with sample 7 set to "
    "(60, -60)")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5], "y": [2.0, 1.0, 3.0]}
    base.update(args)
    cases.append({"id": f"biweight_midcorrelation.{cid}", "op": "biweight_midcorrelation",
                  "args": base, "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0])
err("one_sample", "N must be at least 2", x=[1.0], y=[2.0])
err("zero_mad_x", "x has MAD 0: two of three samples equal", x=[1.0, 1.0, 5.0])
err("zero_mad_y", "y has MAD 0: two of three samples equal", y=[4.0, 0.0, 4.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "biweight_midcorrelation",
    "description": "Biweight midcorrelation (conventions: Biweight midcorrelation; "
                   "ADR 0373).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "biweight_midcorrelation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/biweight_midcorrelation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
