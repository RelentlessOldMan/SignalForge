"""Writes vectors/cases/teager_energy.json, stdlib only.

Teager-Kaiser energy (conventions: Teager-Kaiser energy; ADR 0188): psi[n] = |x[n]|^2 -
Re(x[n-1] conj x[n+1]), n = 1 .. N-2. Expected values come from identities: A cos(W n + p) gives
A^2 sin^2 W exactly (cos^2 a - cos(a-W) cos(a+W) = sin^2 W), A e^{jWn} gives A^2 (1 - cos 2W) =
2 A^2 sin^2 W, r^n gives 0, a ramp gives 1; and from short hand sums.

Run from the repo root: python vectors/generators/teager_energy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, psi, why):
    cases.append({"id": f"teager_energy.{cid}", "op": "teager_energy", "args": {"samples": x},
                  "expected": psi, "tol": TOL, "source": why})


a, w, p = 2.0, 0.7, 0.3
add("cosine", [a * math.cos(w * n + p) for n in range(20)], [a * a * math.sin(w) ** 2] * 18,
    "2 cos(0.7n + 0.3): A^2 sin^2 W = 4 sin^2 0.7 at every n")
a, w = 1.5, 0.4
add("complex_tone", {"re": [a * math.cos(w * n) for n in range(10)],
                     "im": [a * math.sin(w * n) for n in range(10)]},
    [2 * a * a * math.sin(w) ** 2] * 8, "1.5 e^{0.4jn}: 2 A^2 sin^2 W = 4.5 sin^2 0.4")
add("geometric", [0.5 ** n for n in range(8)], [0.0] * 6,
    "0.5^n: 0.25^n - 0.5^{n-1} 0.5^{n+1} = 0, exact in binary")
add("ramp", [0.0, 1.0, 2.0, 3.0, 4.0], [1.0, 1.0, 1.0], "n^2 - (n-1)(n+1) = 1")
add("hand", [1.0, 2.0, 3.0, 5.0], [1.0, -1.0], "4 - 1*3 = 1; 9 - 2*5 = -1")
add("complex_hand", {"re": [1.0, 1.0, 0.0], "im": [0.0, 1.0, 2.0]}, [2.0],
    "x = 1, 1+j, 2j: |1+j|^2 = 2; 1 * conj(2j) = -2j has real part 0; psi = 2")


def err(cid, x, why):
    cases.append({"id": f"teager_energy.{cid}", "op": "teager_energy", "args": {"samples": x},
                  "error": "invalid_argument", "source": why})


err("two", [1.0, 2.0], "fewer than three samples")
err("empty", [], "empty")
err("nan", [1.0, "nan", 0.5], "not finite")

doc = {
    "schema": 1,
    "suite": "teager_energy",
    "description": "Teager-Kaiser energy (conventions: Teager-Kaiser energy; ADR 0188).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "teager_energy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/teager_energy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
