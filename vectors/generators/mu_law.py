"""Writes vectors/cases/mu_law.json, stdlib only.

mu-law companding (conventions: mu-law companding; ADR 0248). Exact anchors for mu = 255:
x = 1/255, 3/255, 15/255, 1 compress to 1/8, 1/4, 1/2, 1 (1 + mu x = 2, 4, 16, 256), and expand
back. Other values are the closed-form curve evaluated with the standard library's log1p and
expm1, checked as a round trip.

Run from the repo root: python vectors/generators/mu_law.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def sign(v):
    return (v > 0) - (v < 0)


def comp(v, mu):
    return sign(v) * (math.log1p(mu * abs(v)) / math.log1p(mu))


def expd(v, mu):
    return sign(v) * (math.expm1(abs(v) * math.log1p(mu)) / mu)


def add(op, cid, x, expected, why, mu=None):
    args = {"samples": x}
    if mu is not None:
        args["mu"] = mu
    cases.append({"id": f"mu_law.{cid}", "op": op, "args": args, "expected": expected,
                  "tol": TOL, "source": why})


anchors_x = [0.0, 1 / 255, 3 / 255, 15 / 255, 1.0, -1 / 255, -15 / 255, -1.0]
anchors_y = [0.0, 0.125, 0.25, 0.5, 1.0, -0.125, -0.5, -1.0]
add("mu_law_compress", "compress_anchors", anchors_x, anchors_y,
    "mu = 255: 1 + mu x = 2, 4, 16, 256 gives 1/8, 1/4, 1/2, 1 exactly (default mu)")
add("mu_law_expand", "expand_anchors", anchors_y, anchors_x,
    "mu = 255: the inverse of the anchors (default mu)")
xs = [0.001, -0.01, 0.1, -0.3, 0.5, 0.9, -0.999]
add("mu_law_compress", "compress_curve", xs, [comp(v, 255.0) for v in xs],
    "closed-form curve, mu = 255, via log1p", mu=255.0)
ys = [0.05, -0.2, 0.4, -0.6, 0.75, 0.95]
add("mu_law_expand", "expand_curve", ys, [expd(v, 255.0) for v in ys],
    "closed-form inverse, mu = 255, via expm1", mu=255.0)
xs8 = [0.25, -0.5, 0.75]
add("mu_law_compress", "compress_mu_100", xs8, [comp(v, 100.0) for v in xs8],
    "closed-form curve, mu = 100", mu=100.0)
for v in xs + xs8:
    for mu in (255.0, 100.0):
        assert abs(expd(comp(v, mu), mu) - v) < 1e-15
for v, w in zip(anchors_x, anchors_y):
    assert abs(comp(v, 255.0) - w) <= 4e-16 * abs(w) and abs(expd(w, 255.0) - v) <= 4e-16 * abs(v)


def err(op, cid, why, **args):
    cases.append({"id": f"mu_law.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("mu_law_compress", "mu_zero", "mu must be positive", samples=[0.5], mu=0.0)
err("mu_law_compress", "out_of_range", "samples must be within [-1, 1]", samples=[1.5])
err("mu_law_expand", "out_of_range_expand", "samples must be within [-1, 1]", samples=[-1.25])
err("mu_law_expand", "empty", "samples must not be empty", samples=[])
err("mu_law_compress", "nan_sample", "samples must be finite", samples=[0.5, "nan"])

doc = {
    "schema": 1,
    "suite": "mu_law",
    "description": "mu-law companding (conventions: mu-law companding; ADR 0248).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mu_law.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mu_law.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
