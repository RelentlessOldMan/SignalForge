"""Writes vectors/cases/cosine_similarity_entropy.json, stdlib only.

Cosine similarity entropy (conventions: Cosine similarity entropy; ADR 0358): every pair's
angular distance in float, asserted at least 1e-9 from r so the count is exact; then the
binary entropy of the share in float.

Run from the repo root: python vectors/generators/cosine_similarity_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, m, r, delay, why):
    w = len(x) - (m - 1) * delay
    vs = [[x[i + k * delay] for k in range(m)] for i in range(w)]
    similar = pairs = 0
    for i in range(w):
        for j in range(i + 1, w):
            dot = math.fsum(a * b for a, b in zip(vs[i], vs[j]))
            na = math.sqrt(math.fsum(a * a for a in vs[i]))
            nb = math.sqrt(math.fsum(b * b for b in vs[j]))
            ang = math.acos(max(-1.0, min(1.0, dot / (na * nb)))) / math.pi
            assert abs(ang - r) > 1e-9, (i, j, ang)
            similar += ang < r
            pairs += 1
    b = similar / pairs
    v = 0.0 if b in (0.0, 1.0) else -b * math.log2(b) - (1 - b) * math.log2(1 - b)
    args = {"samples": x, "m": m, "r": r}
    if delay != 1:
        args["delay"] = delay
    cases.append({"id": f"cosine_similarity_entropy.{cid}", "op": "cosine_similarity_entropy",
                  "args": args, "expected": v, "tol": TOL, "source": why})
    return similar, pairs, v


s, p, v = add("signs_by_hand", [1.0, 2.0, -1.0, 3.0], 1, 0.5, 1,
              "m = 1: angle 0 for the same sign, 1 for opposite; 3 of 6 pairs share a sign, "
              "B = 1/2, one bit")
assert (s, p, v) == (3, 6, 1.0)
s, p, v = add("orthogonal_wide", [1.0, 0.0, 1.0, 0.0], 2, 0.6, 1,
              "vectors (1,0), (0,1), (1,0): angles 1/2, 0, 1/2, all below 0.6: B = 1, 0 bits")
assert (s, p, v) == (3, 3, 0.0)
s, p, v = add("orthogonal_narrow", [1.0, 0.0, 1.0, 0.0], 2, 0.4, 1,
              "the same vectors with r = 0.4: one pair of three, B = 1/3")
assert (s, p) == (1, 3)
assert abs(v - (math.log2(3) - 2 / 3)) < 1e-15
s, p, v = add("delay_2", [1.0, 5.0, 2.0, -1.0, 2.0, 3.0, -0.5, 0.25], 2, 0.1, 2,
              "eight arbitrary samples, m = 2, delay 2, r = 0.1")
rng = random.Random(358)
noise = [rng.randint(-40, 40) / 8 or 0.125 for _ in range(150)]
for m, r in [(2, 0.27), (3, 0.31)]:
    add(f"noise_m{m}", noise, m, r, 1,
        f"150 random eighths from random.Random(358), zeros replaced by 1/8; m = {m}, r = {r}")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, -1.0, 3.0, 0.5], "m": 2, "r": 0.5}
    base.update(args)
    cases.append({"id": f"cosine_similarity_entropy.{cid}", "op": "cosine_similarity_entropy",
                  "args": base, "error": "invalid_argument", "source": why})


err("r_zero", "r must be above 0", r=0.0)
err("r_above_one", "r must be at most 1", r=1.5)
err("m_zero", "m must be at least 1", m=0)
err("one_vector", "W must be at least 2", m=5)
err("zero_vector", "an embedded vector is all zeros", samples=[1.0, 0.0, 0.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "cosine_similarity_entropy",
    "description": "Cosine similarity entropy (conventions: Cosine similarity entropy; ADR 0358).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cosine_similarity_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cosine_similarity_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
