"""Writes vectors/cases/svd_entropy.json, stdlib only.

SVD entropy (conventions: SVD entropy; ADR 0342): the Gram matrix A^T A of the delay embedding
exact in rationals; its eigenvalues in closed form for order 2 (the smaller as det / larger)
and by the cyclic Jacobi eigenvalue method in float otherwise; sigma = sqrt(lambda),
p = sigma / sum, -sum p ln p / ln(order) in float. Every case is asserted well conditioned.

Run from the repo root: python vectors/generators/svd_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def gram(x, m, tau):
    q = [Fr(v) for v in x]
    rows = len(q) - (m - 1) * tau
    cols = [q[j * tau:j * tau + rows] for j in range(m)]
    return [[sum((a * b for a, b in zip(cols[i], cols[j])), Fr(0)) for j in range(m)]
            for i in range(m)]


def eig2(g):
    a, b, c = g[0][0], g[0][1], g[1][1]
    big = (float(a + c) + math.sqrt(float((a - c) ** 2 + 4 * b * b))) / 2
    return [big, float(a * c - b * b) / big]


def jacobi(g):
    a = [[float(v) for v in row] for row in g]
    n = len(a)
    for _ in range(100):
        off = math.fsum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-36 * math.fsum(a[i][i] ** 2 for i in range(n)):
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if a[p][q] == 0:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = math.copysign(1, theta) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
    return [a[i][i] for i in range(n)]


def add(cid, x, m, tau, why):
    g = gram(x, m, tau)
    lam = eig2(g) if m == 2 else jacobi(g)
    assert min(lam) > 1e-6 * max(lam), lam
    tr = sum(g[i][i] for i in range(m))
    assert abs(math.fsum(lam) - float(tr)) < 1e-12 * float(tr)
    s = [math.sqrt(v) for v in lam]
    total = math.fsum(s)
    v = -math.fsum(u / total * math.log(u / total) for u in s) / math.log(m)
    args = {"samples": x, "order": m}
    if tau != 1:
        args["delay"] = tau
    cases.append({"id": f"svd_entropy.{cid}", "op": "svd_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return s, v


s, v = add("orthogonal", [1.0, 0.0, -1.0, 0.0, 1.0], 2, 1, "rows (1,0), (0,-1), (-1,0), (0,1): "
           "A^T A = 2I, two equal singular values, so 1")
assert v == 1.0, v
s, v = add("ramp", [1.0, 2.0, 3.0, 4.0], 2, 1, "rows (1,2), (2,3), (3,4): A^T A = "
           "[[14, 20], [20, 29]], closed form")
assert abs(s[0] ** 2 - (43 + math.sqrt(15 ** 2 + 1600)) / 2) < 1e-12
add("mixed_order_3", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75],
    3, 1, "twelve arbitrary samples, Jacobi on the exact Gram matrix")
rng = random.Random(342)
add("noise_order_5", [rng.randint(-32, 32) / 8 for _ in range(80)], 5, 2,
    "80 random eighths from random.Random(342), order 5, delay 2")
add("square", [0.5, -1.0, 2.0, 0.75, 1.5], 3, 1, "the shortest record for order 3: a 3 x 3 "
    "embedding")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 3.0], "order": 2}
    base.update(args)
    cases.append({"id": f"svd_entropy.{cid}", "op": "svd_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_one", "order must be at least 2", order=1)
err("order_33", "order must be at most 32", order=33)
err("delay_zero", "delay must be at least 1", delay=0)
err("too_short", "K = 6 - 2*2 = 2 < order 3", order=3, delay=2)
err("zeros", "the samples must not all be 0", samples=[0.0] * 6)
err("inf", "samples must be finite", samples=[0.0, "-inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "svd_entropy",
    "description": "SVD entropy (conventions: SVD entropy; ADR 0342).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "svd_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/svd_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
