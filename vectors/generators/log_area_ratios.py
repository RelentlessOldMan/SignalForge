"""Writes vectors/cases/log_area_ratios.json, stdlib only.

Log-area ratios (conventions: Log-area ratios; ADR 0215). g = ln((1 + k)/(1 - k)): the
closed forms k = 1/3 -> ln 2, 3/5 -> ln 4, 4/5 -> ln 9, 9/10 -> ln 19, odd in k; the inverse
k = tanh(g/2) uses the same pairs and, for a large g, (1 - e^-g)/(1 + e^-g) from the stdlib.

Run from the repo root: python vectors/generators/log_area_ratios.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []

ks = [0.0, 1 / 3, 3 / 5, -4 / 5, 9 / 10, -1 / 3]
gs = [0.0, math.log(2), math.log(4), -math.log(9), math.log(19), -math.log(2)]
why = "ln((1 + k)/(1 - k)): 0 -> 0, 1/3 -> ln 2, 3/5 -> ln 4, -4/5 -> -ln 9, 9/10 -> ln 19, " \
    "-1/3 -> -ln 2"
cases.append({"id": "reflection_to_lar.closed_forms", "op": "reflection_to_lar",
              "args": {"reflection": ks}, "expected": gs, "tol": TOL, "source": why})
cases.append({"id": "lar_to_reflection.closed_forms", "op": "lar_to_reflection",
              "args": {"lar": gs}, "expected": ks, "tol": TOL, "source": "the inverse: " + why})
big = 30.0
cases.append({"id": "lar_to_reflection.large", "op": "lar_to_reflection",
              "args": {"lar": [big, -big]},
              "expected": [(1 - math.exp(-big)) / (1 + math.exp(-big)),
                           -(1 - math.exp(-big)) / (1 + math.exp(-big))],
              "tol": TOL, "source": "tanh(15) = (1 - e^-30)/(1 + e^-30), odd"})
cases.append({"id": "reflection_to_lar.near_one", "op": "reflection_to_lar",
              "args": {"reflection": [0.99]}, "expected": [math.log(199)],
              "tol": TOL, "source": "ln(1.99/0.01) = ln 199"})


def err(op, cid, why, **args):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("reflection_to_lar", "unit_k", "every |k| < 1", reflection=[0.5, -1.0])
err("reflection_to_lar", "empty", "reflection must not be empty", reflection=[])
err("reflection_to_lar", "nan", "reflection must be finite", reflection=["nan"])
err("lar_to_reflection", "empty", "lar must not be empty", lar=[])
err("lar_to_reflection", "inf", "lar must be finite", lar=[1.0, "inf"])

doc = {
    "schema": 1,
    "suite": "log_area_ratios",
    "description": "Log-area ratios (conventions: Log-area ratios; ADR 0215).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "log_area_ratios.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/log_area_ratios.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
