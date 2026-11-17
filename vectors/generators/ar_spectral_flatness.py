"""Writes vectors/cases/ar_spectral_flatness.json, stdlib only.

Spectral flatness of an AR model (conventions: Spectral flatness of an AR model; ADR 0213).
The expected value is prod(1 - |k|^2) in exact fractions (or with complex). Each case is
cross-checked by integrating S = 1/|A(e^jw)|^2 numerically: exp(mean ln S) / mean S on a
4096-point grid, with A from the step-up recursion.

Run from the repo root: python vectors/generators/ar_spectral_flatness.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def stepup(k):
    a = [1 + 0j]
    for km in k:
        a = a + [0j]
        a = [a[j] + complex(km) * a[len(a) - 1 - j].conjugate() for j in range(len(a))]
    return a


def numeric(k):
    a = stepup(k)
    grid = 4096
    s = []
    for i in range(grid):
        w = 2 * math.pi * i / grid
        h = sum(c * cmath.exp(-1j * w * j) for j, c in enumerate(a))
        s.append(1 / abs(h) ** 2)
    return math.exp(sum(math.log(v) for v in s) / grid) / (sum(s) / grid)


def exact(k):
    out = Fr(1)
    for v in k:
        out *= 1 - (v * v if isinstance(v, Fr) else Fr(abs(v) ** 2))
    return out


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, k, why):
    if any(isinstance(v, complex) for v in k):
        value = 1.0
        for v in k:
            value *= 1 - abs(v) ** 2
    else:
        value = float(exact(k))
    assert abs(numeric(k) - value) < 1e-9, (cid, numeric(k), value)
    cases.append({"id": f"ar_spectral_flatness.{cid}", "op": "ar_spectral_flatness",
                  "args": {"reflection": enc(k)}, "expected": value, "tol": TOL, "source": why})


add("white", [Fr(0)], "k = 0: A = 1, a flat spectrum, flatness 1")
add("order_one", [Fr(-1, 2)], "1 - 1/4 = 3/4")
add("order_two", [Fr(1, 2), Fr(-3, 10)], "(3/4)(91/100) = 273/400")
add("burg_three_samples", [Fr(-8, 9), Fr(77, 85)],
    "ADR 0205's x = [1, 2, 3]: (17/81)(1296/7225) = 22032/585225")
add("order_three", [Fr(1, 2), Fr(-1, 3), Fr(1, 4)], "(3/4)(8/9)(15/16) = 5/8")
add("near_unit", [Fr(99, 100)], "1 - 9801/10000 = 199/10000, a sharp peak")
add("complex", [0.3 + 0.4j, -0.2 + 0.1j], "|k|^2 = 1/4 and 1/20: (3/4)(19/20)")
assert exact([Fr(-8, 9), Fr(77, 85)]) == Fr(22032, 585225)
assert exact([Fr(1, 2), Fr(-1, 3), Fr(1, 4)]) == Fr(5, 8)


def err(cid, why, **args):
    cases.append({"id": f"ar_spectral_flatness.{cid}", "op": "ar_spectral_flatness",
                  "args": args, "error": "invalid_argument", "source": why})


err("unit_k", "every |k| < 1", reflection=[0.5, -1.0])
err("empty", "reflection must not be empty", reflection=[])
err("nan", "reflection must be finite", reflection=[0.5, "nan"])

doc = {
    "schema": 1,
    "suite": "ar_spectral_flatness",
    "description": "Spectral flatness of an AR model (conventions: Spectral flatness of an AR"
    " model; ADR 0213).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ar_spectral_flatness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ar_spectral_flatness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
