"""Writes vectors/cases/renyi_entropy.json, stdlib only.

Rényi entropy (conventions: Rényi entropy; ADR 0353): each dyadic sample's bin exact in
rationals as in ADR 0352, with the same near-edge assert; exact counts; then ln K, -sum p ln p
or ln(sum p^alpha) / (1 - alpha) in float.

Run from the repo root: python vectors/generators/renyi_entropy.py [--check]
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


def add(cid, x, alpha, bins, why):
    assert alpha in (0, 1) or abs(alpha - 1) >= 0.5
    q = [Fr(v) for v in x]
    lo, hi = min(q), max(q)
    b = []
    for u in q:
        t = (u - lo) * bins / (hi - lo)
        if t < bins and t.denominator != 1:
            assert abs(float(t) - round(float(t))) > 1e-9, t
        b.append(min(bins - 1, math.floor(t)))
    p = [c / len(b) for c in Counter(b).values()]
    if alpha == 0:
        v = math.log(len(p))
    elif alpha == 1:
        v = -math.fsum(u * math.log(u) for u in p)
    else:
        v = math.log(math.fsum(u ** alpha for u in p)) / (1 - alpha)
    args = {"samples": x, "alpha": alpha}
    if bins != 16:
        args["bins"] = bins
    cases.append({"id": f"renyi_entropy.{cid}", "op": "renyi_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return v


for a in [0.0, 0.5, 1.0, 2.0]:
    v = add(f"uniform_alpha_{a:g}", [0.0, 1.0, 2.0, 3.0], a, 4,
            "one sample in each of four bins: ln 4 at every order")
    assert abs(v - math.log(4)) < 1e-15, (a, v)
v = add("collision_by_hand", [0.0, 0.0, 0.0, 1.0], 2.0, 2,
        "shares 3/4 and 1/4: -ln(9/16 + 1/16) = ln(8/5)")
assert abs(v - math.log(8 / 5)) < 1e-15
v = add("occupied_bins", [0.0, 0.0, 0.0, 0.25, 1.0], 0.0, 8,
        "bins 0, 0, 0, 2, 7: three occupied, so ln 3")
assert v == math.log(3)
rng = random.Random(353)
noise = [rng.randint(-60, 60) / 16 for _ in range(300)]
for a in [0.0, 0.25, 1.0, 3.5]:
    add(f"noise_alpha_{a:g}", noise, a, 16,
        f"300 random sixteenths from random.Random(353), the default 16 bins, order {a:g}")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "alpha": 2.0}
    base.update(args)
    cases.append({"id": f"renyi_entropy.{cid}", "op": "renyi_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("alpha_negative", "alpha must be at least 0", alpha=-0.5)
err("alpha_inf", "alpha must be finite", alpha="inf")
err("one_bin", "bins must be at least 2", bins=1)
err("constant", "samples must not all be equal", samples=[2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "renyi_entropy",
    "description": "Rényi entropy (conventions: Rényi entropy; ADR 0353).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "renyi_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/renyi_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
