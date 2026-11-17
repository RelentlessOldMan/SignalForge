"""Writes vectors/cases/thiran_allpass.json, stdlib only.

Thiran allpass (conventions: Thiran allpass; ADR 0227). a_k = (-1)^k C(N, k)
prod_n (D - N + n) / (D - N + k + n) in exact fractions. Each case is checked against the DC group
delay of z^-N A(1/z) / A(z), N - 2 sum k a_k / sum a_k, which must be D; order 1 also against the
textbook a_1 = (1 - D) / (1 + D).

Run from the repo root: python vectors/generators/thiran_allpass.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def thiran(d, n):
    a = [Fr(1)]
    for k in range(1, n + 1):
        v = Fr((-1) ** k * math.comb(n, k))
        for m in range(n + 1):
            v *= (d - n + m) / (d - n + k + m)
        a.append(v)
    assert a[0] == 1
    assert n - 2 * sum(k * ak for k, ak in enumerate(a)) / sum(a) == d, (d, n)
    return a


def add(cid, d, n, why):
    a = thiran(d, n)
    cases.append({"id": f"thiran_allpass.{cid}", "op": "thiran_allpass",
                  "args": {"delay": float(d), "order": n}, "expected": [float(v) for v in a],
                  "tol": TOL, "source": why})
    return a


assert add("first_order", Fr(1, 2), 1, "order 1, D = 1/2: a_1 = (1 - D)/(1 + D) = 1/3") == [
    1, Fr(1, 3)]
assert add("pure_delay", Fr(3), 3, "D = N: the pure delay z^-3") == [1, 0, 0, 0]
add("second_order", Fr(3, 2), 2, "order 2, D = 3/2")
add("third_order", Fr(13, 4), 3, "order 3, D = 13/4")
add("near_limit", Fr(41, 40), 2, "order 2, D = 1.025, just above N - 1")
add("order_six", Fr(57, 10), 6, "order 6, D = 5.7")


def err(cid, why, **args):
    cases.append({"id": f"thiran_allpass.{cid}", "op": "thiran_allpass", "args": args,
                  "error": "invalid_argument", "source": why})


err("at_limit", "delay must be greater than order - 1", delay=1.0, order=2)
err("below_limit", "delay must be greater than order - 1", delay=0.5, order=2)
err("order_zero", "order must be at least 1", delay=0.5, order=0)
err("nan_delay", "delay must be finite", delay="nan", order=2)
err("inf_delay", "delay must be finite", delay="inf", order=2)

doc = {
    "schema": 1,
    "suite": "thiran_allpass",
    "description": "Thiran allpass (conventions: Thiran allpass; ADR 0227).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "thiran_allpass.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/thiran_allpass.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
