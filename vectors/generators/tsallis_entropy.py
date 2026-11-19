"""Writes vectors/cases/tsallis_entropy.json, stdlib only.

Tsallis entropy (conventions: Tsallis entropy; ADR 0356): each dyadic sample's bin exact in
rationals as in ADR 0352, with the same near-edge assert; exact counts; then -sum p ln p or
(1 - sum p^q) / (q - 1) in float.

Run from the repo root: python vectors/generators/tsallis_entropy.py [--check]
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


def add(cid, x, q, bins, why):
    assert q == 1 or abs(q - 1) >= 0.5
    r = [Fr(v) for v in x]
    lo, hi = min(r), max(r)
    b = []
    for u in r:
        t = (u - lo) * bins / (hi - lo)
        if t < bins and t.denominator != 1:
            assert abs(float(t) - round(float(t))) > 1e-9, t
        b.append(min(bins - 1, math.floor(t)))
    p = [c / len(b) for c in Counter(b).values()]
    if q == 1:
        v = -math.fsum(u * math.log(u) for u in p)
    else:
        v = (1 - math.fsum(u ** q for u in p)) / (q - 1)
    args = {"samples": x, "q": q}
    if bins != 16:
        args["bins"] = bins
    cases.append({"id": f"tsallis_entropy.{cid}", "op": "tsallis_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return v


v = add("q0_counts_bins", [0.0, 0.0, 0.0, 0.25, 1.0], 0.0, 8,
        "bins 0, 0, 0, 2, 7: three occupied, so K - 1 = 2")
assert v == 2.0
v = add("q2_by_hand", [0.0, 0.0, 0.0, 1.0], 2.0, 2,
        "shares 3/4 and 1/4: 1 - 9/16 - 1/16 = 3/8")
assert v == 0.375
v = add("uniform_q1", [0.0, 1.0, 2.0, 3.0], 1.0, 4, "four equal shares at q = 1: ln 4")
assert abs(v - math.log(4)) < 1e-15
v = add("uniform_q3", [0.0, 1.0, 2.0, 3.0], 3.0, 4,
        "four equal shares at q = 3: (1 - 4/64)/2 = 15/32")
assert v == 15 / 32
rng = random.Random(356)
noise = [rng.randint(-60, 60) / 16 for _ in range(300)]
for q in [0.0, 0.5, 1.0, 2.5]:
    add(f"noise_q_{q:g}", noise, q, 16,
        f"300 random sixteenths from random.Random(356), the default 16 bins, q = {q:g}")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "q": 2.0}
    base.update(args)
    cases.append({"id": f"tsallis_entropy.{cid}", "op": "tsallis_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("q_negative", "q must be at least 0", q=-0.5)
err("q_inf", "q must be finite", q="inf")
err("one_bin", "bins must be at least 2", bins=1)
err("constant", "samples must not all be equal", samples=[2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "tsallis_entropy",
    "description": "Tsallis entropy (conventions: Tsallis entropy; ADR 0356).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tsallis_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tsallis_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
