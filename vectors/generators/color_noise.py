"""Writes vectors/cases/color_noise.json, stdlib only.

Colored noise (conventions: Colored noise; ADR 0318). The gain g_k = min(k, N - k)^(-a/2),
g_0 = 0, is real and even, so the shaping is the circular convolution of the samples with
h[j] = (1/N) sum_k g_k cos(2 pi k j / N), computed here directly with math.cos and math.fsum,
without an FFT.

Run from the repo root: python vectors/generators/color_noise.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def shape(x, a):
    n = len(x)
    g = [0.0 if min(k, n - k) == 0 else min(k, n - k) ** (-a / 2) for k in range(n)]
    h = [math.fsum(g[k] * math.cos(2 * math.pi * k * j / n) for k in range(n)) / n
         for j in range(n)]
    return [math.fsum(x[m] * h[(i - m) % n] for m in range(n)) for i in range(n)]


def add(cid, x, a, why):
    y = shape(x, a)
    cases.append({"id": f"color_noise.{cid}", "op": "color_noise",
                  "args": {"white": x, "exponent": a}, "expected": y, "tol": TOL,
                  "source": why})
    return y


x8 = [0.5, -1.25, 2.0, 0.75, -0.5, 1.5, -2.0, 0.25]
x9 = [1.0, 0.0, -0.5, 0.25, 0.5, -1.0, 0.75, -0.25, 0.125]
y = add("white_less_mean", x8, 0.0, "exponent 0: the samples less their mean, 1.25/8")
assert all(abs(a - (b - 1.25 / 8)) < 1e-13 for a, b in zip(y, x8, strict=True)), y
add("pink_even", x8, 1.0, "pink, N = 8: bin 4 is the Nyquist bin, scaled by 4^(-1/2)")
add("brown_odd", x9, 2.0, "brown, N = 9: no Nyquist bin")
add("blue", x9, -1.0, "blue: the high bins are raised")
add("impulse", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], 1.5, "an impulse: the output is h itself")
add("one", [3.0], 1.0, "N = 1: only bin 0, set to 0")
add("empty", [], 1.0, "no samples: nothing out")


def err(cid, why, **args):
    base = {"white": [1.0, 2.0, 3.0], "exponent": 1.0}
    base.update(args)
    cases.append({"id": f"color_noise.{cid}", "op": "color_noise", "args": base,
                  "error": "invalid_argument", "source": why})


err("exponent_infinite", "exponent must be finite", exponent="inf")

doc = {
    "schema": 1,
    "suite": "color_noise",
    "description": "Colored noise (conventions: Colored noise; ADR 0318).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "color_noise.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/color_noise.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
