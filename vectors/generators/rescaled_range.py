"""Writes vectors/cases/rescaled_range.json, stdlib only.

Rescaled range (conventions: Rescaled range; ADR 0340): per scale, each box's R = max Z - min Z
of the cumulative mean-removed sums and S^2 = sum y^2 / s exact in rationals from dyadic
samples; then R / sqrt(S^2), the mean over boxes (math.fsum), logs and the least-squares slope
in float.

Run from the repo root: python vectors/generators/rescaled_range.py [--check]
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


def rs(x, s):
    q = [Fr(v) for v in x]
    ratios = []
    for b in range(len(q) // s):
        box = q[b * s:(b + 1) * s]
        mean = sum(box, Fr(0)) / s
        y = [v - mean for v in box]
        z, run = [], Fr(0)
        for v in y:
            run += v
            z.append(run)
        assert z[-1] == 0
        r = max(z) - min(z)
        s2 = sum((v * v for v in y), Fr(0)) / s
        ratios.append(float(r) / math.sqrt(s2))
    return math.fsum(ratios) / len(ratios)


def add(cid, x, scales, why):
    values = [rs(x, s) for s in scales]
    lx = [math.log(s) for s in scales]
    ly = [math.log(v) for v in values]
    mx, my = math.fsum(lx) / len(lx), math.fsum(ly) / len(ly)
    hurst = (math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
             / math.fsum((a - mx) ** 2 for a in lx))
    cases.append({"id": f"rescaled_range.{cid}", "op": "rescaled_range",
                  "args": {"samples": x, "scales": scales},
                  "expected": {"scales": scales, "values": values, "hurst": hurst},
                  "tol": TOL, "source": why})
    return values


v = add("alternating", [1.0, -1.0] * 8, [4, 8, 16], "+-1 alternating: Z = 1, 0, 1, 0, ..., "
        "so R = 1 and S = 1 in every box: values 1, hurst 0")
assert v == [1.0, 1.0, 1.0], v
v = add("ramp", [float(i) for i in range(8)], [4, 8], "a ramp: at s = 4, y = -1.5 .. 1.5, "
        "Z = -1.5, -2, -1.5, 0, R = 2, S^2 = 5/4")
assert abs(v[0] - 2 / math.sqrt(1.25)) < 1e-15, v
rng = random.Random(340)
add("noise", [rng.randint(-16, 16) / 8 for _ in range(64)], [4, 8, 16, 32, 64],
    "64 random eighth-integers from random.Random(340)")
add("leftover", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75,
                 0.0, 1.5, -0.75], [5, 7], "fifteen arbitrary samples; s = 7 leaves one over")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 3.0, -1.0, 0.25], "scales": [4, 8]}
    base.update(args)
    cases.append({"id": f"rescaled_range.{cid}", "op": "rescaled_range", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_scale", "at least two scales are needed", scales=[4])
err("scale_three", "each scale must be at least 4", scales=[3, 4])
err("scale_too_big", "each scale must be at most N", scales=[4, 9])
err("repeated", "scales must be strictly increasing", scales=[4, 4])
err("flat_box", "the first box is constant, S = 0",
    samples=[2.0, 2.0, 2.0, 2.0, 1.5, 3.0, -1.0, 0.25])

doc = {
    "schema": 1,
    "suite": "rescaled_range",
    "description": "Rescaled range and the Hurst exponent (conventions: Rescaled range; "
                   "ADR 0340).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rescaled_range.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/rescaled_range.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
