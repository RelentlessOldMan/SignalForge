"""Writes vectors/cases/ar_order_selection.json, stdlib only.

AR order selection (conventions: AR order selection; ADR 0206). The errors come from the
forward/backward Burg recursion written out here with plain lists (exact fractions for
x = [1, 2, 3] and for the impulse); FPE and AIC follow from their definitions.

Run from the repo root: python vectors/generators/ar_order_selection.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def errors_of(x, top):
    f = [complex(v) for v in x]
    b = list(f)
    errs = [sum(abs(v) ** 2 for v in f) / len(f)]
    for _ in range(top):
        fw, bw = f[1:], b[:-1]
        k = -2 * sum(u * v.conjugate() for u, v in zip(fw, bw)) / sum(
            abs(u) ** 2 + abs(v) ** 2 for u, v in zip(fw, bw))
        f = [u + k * v for u, v in zip(fw, bw)]
        b = [v + k.conjugate() * u for u, v in zip(fw, bw)]
        errs.append(errs[-1] * (1 - abs(k) ** 2))
    return errs


def add(cid, x, top, why, errs=None):
    is_complex = any(isinstance(v, complex) for v in x)
    n = len(x)
    errs = errors_of(x, top) if errs is None else errs
    fpe = [errs[p] * Fr(n + p + 1, n - p - 1) if isinstance(errs[p], Fr)
           else errs[p] * (n + p + 1) / (n - p - 1) for p in range(top + 1)]
    aic = [n * math.log(errs[p]) + 2 * p for p in range(top + 1)]
    best = [min(range(top + 1), key=lambda p, v=v: (v[p], p)) for v in (fpe, aic)]
    for v, o in zip((fpe, aic), best):
        others = [float(v[p]) - float(v[o]) for p in range(top + 1) if p != o]
        assert all(d > 1e-9 for d in others), (cid, v)
    args = {"samples": ({"re": [complex(v).real for v in x], "im": [complex(v).imag for v in x]}
                        if is_complex else x), "max_order": top}
    cases.append({"id": f"ar_order_selection.{cid}", "op": "ar_order_selection", "args": args,
                  "expected": {"errors": [float(e) for e in errs], "fpe": [float(e) for e in fpe],
                               "aic": aic, "fpe_order": best[0], "aic_order": best[1]},
                  "tol": TOL, "source": why})


e3 = [Fr(14, 3), Fr(14, 3) * (1 - Fr(8, 9) ** 2)]
assert abs(errors_of([1.0, 2.0, 3.0], 1)[1] - float(e3[1])) < 1e-15
add("three_samples", [1.0, 2.0, 3.0], 1,
    "x = [1, 2, 3]: s0 = 14/3, k1 = -8/9, s1 = (14/3)(17/81); FPE = 28/3, 1190/243; "
    "AIC = 3 ln s + 2p: both pick order 1", e3)
add("impulse", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], 3,
    "an impulse: every k = 0, so s_p = 1/6; FPE (7 + p)/(5 - p)/6 and AIC rise with p: order 0",
    [Fr(1, 6)] * 4)
add("real_order_four", [3.0, 1.0, -2.0, 0.0, 1.0, 2.5, -1.5, 0.5, 2.0, -1.0], 4,
    "Burg errors by the stdlib recursion; FPE and AIC from their definitions")
add("complex", [1 + 1j, -0.5 + 2j, 1.5 - 1j, 0.25j, -1 + 0j, 0.5 - 0.5j], 3,
    "complex: Burg errors by the stdlib recursion with conj(k) in the backward update")


def err(cid, why, **args):
    cases.append({"id": f"ar_order_selection.{cid}", "op": "ar_order_selection", "args": args,
                  "error": "invalid_argument", "source": why})


err("max_order_zero", "max_order must be at least 1", samples=[1.0, 2.0, 3.0], max_order=0)
err("max_order_too_big", "max_order must be at most N - 2", samples=[1.0, 2.0, 3.0], max_order=2)
err("all_zero", "the error energy is 0", samples=[0.0, 0.0, 0.0], max_order=1)
err("predictable", "x = [1, -1, 1]: k1 = -2(-2)/4 = 1", samples=[1.0, -1.0, 1.0], max_order=1)
err("nan_sample", "samples must be finite", samples=[1.0, "nan", 2.0], max_order=1)

doc = {
    "schema": 1,
    "suite": "ar_order_selection",
    "description": "AR order selection (conventions: AR order selection; ADR 0206).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ar_order_selection.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ar_order_selection.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
