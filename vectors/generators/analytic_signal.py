"""Writes vectors/cases/analytic_signal.json, stdlib only.

Analytic signal (conventions: Analytic signal; ADR 0185): z = ifft(fft(x) W), W[0] = 1,
W[k] = 2 for 0 < 2k < N, W[N/2] = 1 for even N, 0 above. Expected values are closed forms at
bin frequencies (cos -> e^{j theta}, sin -> -j e^{j theta}, DC and Nyquist unchanged) and hand
DFT sums of impulses.

Run from the repo root: python vectors/generators/analytic_signal.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, z, why):
    cases.append({"id": f"analytic_signal.{cid}", "op": "analytic_signal",
                  "args": {"samples": x},
                  "expected": {"re": [v.real for v in z], "im": [v.imag for v in z]},
                  "tol": TOL, "source": why})


def tone(n, k, phase, kind):
    th = [2 * math.pi * k * i / n + phase for i in range(n)]
    if kind == "cos":
        return [math.cos(t) for t in th], [cmath.exp(1j * t) for t in th]
    return [math.sin(t) for t in th], [-1j * cmath.exp(1j * t) for t in th]


add("cos_even", *tone(8, 1, 0.3, "cos"), "cos(2 pi n/8 + 0.3) -> e^{j(2 pi n/8 + 0.3)}")
add("sin_even", *tone(16, 3, 0.0, "sin"), "sin(2 pi 3n/16) -> -j e^{j 2 pi 3n/16}")
add("cos_odd", *tone(5, 2, -0.7, "cos"), "N = 5, bin 2 < 5/2: cos -> e^{j theta}")
x = [3.0, 1.0, 3.0, 1.0]
add("dc_nyquist", x, [complex(v) for v in x],
    "2 + (-1)^n: only bins 0 and N/2, both weight 1: unchanged and real")
add("impulse4", [1.0, 0.0, 0.0, 0.0], [1, 0.5j, 0, -0.5j],
    "X = 1 1 1 1, W = 1 2 1 0: z[n] = (1 + 2 j^n + (-1)^n)/4 = 1, j/2, 0, -j/2")
r = 1 / math.sqrt(3)
add("impulse3", [1.0, 0.0, 0.0], [1, r * 1j, -r * 1j],
    "X = 1 1 1, W = 1 2 0: z[n] = (1 + 2 e^{j 2 pi n/3})/3 = 1, j/sqrt 3, -j/sqrt 3")
add("single", [2.5], [2.5], "N = 1: W = 1, the sample itself")


def err(cid, x, why):
    cases.append({"id": f"analytic_signal.{cid}", "op": "analytic_signal",
                  "args": {"samples": x}, "error": "invalid_argument", "source": why})


err("empty", [], "empty")
err("nan", [1.0, "nan", 0.0], "not finite")
err("inf", [1.0, 0.0, "-inf"], "not finite")

doc = {
    "schema": 1,
    "suite": "analytic_signal",
    "description": "Analytic signal (conventions: Analytic signal; ADR 0185).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "analytic_signal.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/analytic_signal.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
