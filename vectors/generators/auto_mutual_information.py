"""Writes vectors/cases/auto_mutual_information.json, stdlib only.

Auto mutual information (conventions: Auto mutual information; ADR 0352): each dyadic sample's
bin min(B - 1, floor((x - lo) B / (hi - lo))) exact in rationals, asserting no position below
B is within 1e-9 of an integer unless it is exactly one; exact joint and marginal counts at
each lag; then sum (c_ab/n) ln(c_ab n / (c_a c_b)) in float.

Run from the repo root: python vectors/generators/auto_mutual_information.py [--check]
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


def add(cid, x, lags, bins, why):
    q = [Fr(v) for v in x]
    lo, hi = min(q), max(q)
    b = []
    for u in q:
        t = (u - lo) * bins / (hi - lo)
        if t < bins and t.denominator != 1:
            assert abs(float(t) - round(float(t))) > 1e-9, t
        b.append(min(bins - 1, math.floor(t)))
    out = []
    for tau in lags:
        n = len(b) - tau
        pairs = list(zip(b[:n], b[tau:]))
        ca = Counter(p[0] for p in pairs)
        cb = Counter(p[1] for p in pairs)
        out.append(math.fsum(c / n * math.log(c * n / (ca[a] * cb[d]))
                             for (a, d), c in Counter(pairs).items()))
    args = {"samples": x, "lags": lags}
    if bins != 16:
        args["bins"] = bins
    cases.append({"id": f"auto_mutual_information.{cid}", "op": "auto_mutual_information",
                  "args": args, "expected": out, "tol": TOL, "source": why})
    return b, out


b, out = add("two_levels", [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0], [0, 1, 2, 7], 2,
             "alternating 0, 1 in two bins: lag 0 is the entropy ln 2; at lag 1 each of the seven "
             "pairs fixes the other level, so the entropy of (4/7, 3/7); at lag 2, of (1/2, "
             "1/2), ln 2; lag 7 has one pair, so 0")
assert b == [0, 1] * 4
h47 = -(4 / 7 * math.log(4 / 7) + 3 / 7 * math.log(3 / 7))
assert abs(out[0] - math.log(2)) < 1e-15 and abs(out[1] - h47) < 1e-15, out
assert abs(out[2] - math.log(2)) < 1e-15 and out[3] == 0.0, out
b, out = add("independent_by_hand", [0.0, 0.0, 1.0, 1.0, 0.0], [1], 2,
             "pairs (0,0), (0,1), (1,1), (1,0): every joint bin once, marginals 2 and 2, so 0")
assert out == [0.0], out
add("top_edge", [0.0, 0.25, 0.5, 0.75, 1.0, 0.5, 0.0, 1.0], [0, 1, 3], 4,
    "samples on every bin edge; the maximum goes in the last bin")
rng = random.Random(352)
add("noise", [rng.randint(-60, 60) / 16 for _ in range(400)], [5, 0, 1, 2, 10], 16,
    "400 random sixteenths from random.Random(352), the default 16 bins, lags out of order")
walk = [0.0]
for _ in range(299):
    walk.append(walk[-1] + rng.choice([-0.5, 0.5]))
add("walk", walk, [1, 4, 16, 64], 12, "a 300-step random walk of half steps, 12 bins")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "lags": [1]}
    base.update(args)
    cases.append({"id": f"auto_mutual_information.{cid}", "op": "auto_mutual_information",
                  "args": base, "error": "invalid_argument", "source": why})


err("no_lags", "lags must have at least one entry", lags=[])
err("lag_negative", "a lag must be at least 0", lags=[-1])
err("lag_too_big", "a lag must be at most N - 1", lags=[5])
err("one_bin", "bins must be at least 2", bins=1)
err("bins_4097", "bins must be at most 4096", bins=4097)
err("constant", "samples must not all be equal", samples=[2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "auto_mutual_information",
    "description": "Auto mutual information (conventions: Auto mutual information; ADR 0352).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "auto_mutual_information.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/auto_mutual_information.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
