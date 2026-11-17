"""Writes vectors/cases/arcsine_coefficients.json, stdlib only.

Inverse sine coefficients (conventions: Inverse sine coefficients; ADR 0216). theta = arcsin k:
the closed forms 1/2 -> pi/6, sqrt(2)/2 -> pi/4, sqrt(3)/2 -> pi/3, odd in k; the inverse
k = sin theta uses the same pairs.

Run from the repo root: python vectors/generators/arcsine_coefficients.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []

ks = [0.0, 0.5, math.sqrt(2) / 2, -math.sqrt(3) / 2, -0.5]
ts = [0.0, math.pi / 6, math.pi / 4, -math.pi / 3, -math.pi / 6]
why = "arcsin: 0 -> 0, 1/2 -> pi/6, sqrt(2)/2 -> pi/4, -sqrt(3)/2 -> -pi/3, -1/2 -> -pi/6"
cases.append({"id": "reflection_to_arcsine.closed_forms", "op": "reflection_to_arcsine",
              "args": {"reflection": ks}, "expected": ts, "tol": TOL, "source": why})
cases.append({"id": "arcsine_to_reflection.closed_forms", "op": "arcsine_to_reflection",
              "args": {"arcsine": ts}, "expected": ks, "tol": TOL, "source": "the inverse: " + why})


def err(op, cid, why, **args):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("reflection_to_arcsine", "unit_k", "every |k| < 1", reflection=[0.5, 1.0])
err("reflection_to_arcsine", "empty", "reflection must not be empty", reflection=[])
err("reflection_to_arcsine", "nan", "reflection must be finite", reflection=["nan"])
err("arcsine_to_reflection", "half_pi", "every |theta| < pi/2", arcsine=[0.1, -2.0])
err("arcsine_to_reflection", "empty", "arcsine must not be empty", arcsine=[])
err("arcsine_to_reflection", "inf", "arcsine must be finite", arcsine=["inf"])

doc = {
    "schema": 1,
    "suite": "arcsine_coefficients",
    "description": "Inverse sine coefficients (conventions: Inverse sine coefficients; ADR 0216).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "arcsine_coefficients.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/arcsine_coefficients.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
