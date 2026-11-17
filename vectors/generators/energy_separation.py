"""Writes vectors/cases/energy_separation.json, stdlib only.

Energy separation (conventions: Energy separation; ADR 0189): DESA-2 with y[n] = x[n+1] -
x[n-1], c = 1 - psi[y]/(2 psi[x]) clamped to [-1, 1], frequency acos(c)/2 fs/(2 pi), amplitude
2 psi[x]/sqrt(psi[y]); NaN where an energy is not positive. Expected values come from the cosine
identity (psi[x] = A^2 sin^2 W, psi[y] = 4 A^2 sin^4 W, so exactly A and W fs/(2 pi)) and from
five-sample hand sums.

Run from the repo root: python vectors/generators/energy_separation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-10, "rel": 1e-10}
cases = []


def add(cid, x, fs, amp, freq, why):
    cases.append({"id": f"energy_separation.{cid}", "op": "energy_separation",
                  "args": {"samples": x, "sample_rate": fs},
                  "expected": {"amplitude": amp, "frequency": freq}, "tol": TOL,
                  "source": why})


a, w, p, n_ = 2.0, 0.7, 0.3, 16
add("cosine", [a * math.cos(w * n + p) for n in range(n_)], 1000.0, [a] * (n_ - 4),
    [w * 1000.0 / (2 * math.pi)] * (n_ - 4),
    "2 cos(0.7n + 0.3) at 1 kHz: exactly A = 2 and 0.7 * 1000/(2 pi) Hz at every n")
a, w, n_ = 0.5, 1.2, 12
add("cosine_fast", [a * math.cos(w * n) for n in range(n_)], 48000.0, [a] * (n_ - 4),
    [w * 48000.0 / (2 * math.pi)] * (n_ - 4), "0.5 cos(1.2n) at 48 kHz: A = 0.5, 1.2 rad/sample")
add("impulse", [0.0, 0.0, 1.0, 0.0, 0.0], 12.0, [2.0], [1.0],
    "psi[x] = 1 - 0 = 1; y = 1, 0, -1 so psi[y] = 0 + 1 = 1; c = 1/2, acos/2 = pi/6, "
    "pi/6 * 12/(2 pi) = 1 Hz; amplitude 2/1 = 2")
add("quarter_rate", [-1.0, 0.0, 1.0, 0.0, -1.0], 8.0, [1.0], [2.0],
    "cos(pi(n-2)/2): psi[x] = 1; y = 2, 0, -2 so psi[y] = 4; c = -1 exactly, acos/2 = pi/2, "
    "fs/4 = 2 Hz; amplitude 2/2 = 1")
add("clamped", [-2.0, 0.0, 1.0, 0.0, -2.0], 8.0, [2 / 3], [2.0],
    "psi[x] = 1; y = 3, 0, -3 so psi[y] = 9; c = 1 - 4.5 < -1 is clamped to -1: fs/4 = 2 Hz; "
    "amplitude 2/3")
add("constant", [1.0] * 6, 10.0, ["nan", "nan"], ["nan", "nan"],
    "a constant: psi[x] = 1 - 1 = 0 and y = 0, so no estimate: NaN")
add("fibonacci", [1.0, 1.0, 2.0, 3.0, 5.0, 8.0], 12.0, [2.0, "nan"], [1.0, "nan"],
    "y[1..4] = 1, 2, 3, 5. n = 2: psi[x] = 4 - 1*3 = 1, psi[y] = 2^2 - 1*3 = 1, c = 1/2: "
    "pi/6 * 12/(2 pi) = 1 Hz, amplitude 2. n = 3: psi[x] = 9 - 2*5 = -1: NaN")


def err(cid, x, fs, why):
    cases.append({"id": f"energy_separation.{cid}", "op": "energy_separation",
                  "args": {"samples": x, "sample_rate": fs}, "error": "invalid_argument",
                  "source": why})


err("four", [1.0, 0.0, -1.0, 0.0], 10.0, "fewer than five samples")
err("zero_rate", [0.0, 0.0, 1.0, 0.0, 0.0], 0.0, "sample_rate must be positive")
err("nan", [0.0, 0.0, "nan", 0.0, 0.0], 10.0, "not finite")

doc = {
    "schema": 1,
    "suite": "energy_separation",
    "description": "Energy separation (conventions: Energy separation; ADR 0189).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "energy_separation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/energy_separation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
