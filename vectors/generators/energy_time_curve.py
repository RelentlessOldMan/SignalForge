"""Writes vectors/cases/energy_time_curve.json, stdlib only.

Energy-time curve (conventions: Energy-time curve; ADR 0186): 10 log10(|z|^2 / max |z|^2) with
z the analytic signal of ADR 0185. Expected values are closed forms: hand analytic signals of
impulses (and their circular shifts), the exact envelope 1 + m cos of an AM tone at bin
frequencies, and a constant.

Run from the repo root: python vectors/generators/energy_time_curve.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-10, "rel": 1e-12}
cases = []


def db(r):
    return "-inf" if r == 0 else 10 * math.log10(r)


def add(cid, h, ratios, why, tol=TOL):
    cases.append({"id": f"energy_time_curve.{cid}", "op": "energy_time_curve",
                  "args": {"impulse_response": h},
                  "expected": [db(r) for r in ratios], "tol": tol, "source": why})


add("impulse4", [1.0, 0.0, 0.0, 0.0], [1, 0.25, 0, 0.25],
    "z = 1, j/2, 0, -j/2 (ADR 0185): |z|^2 = 1, 1/4, 0, 1/4 of the peak")
add("shifted4", [0.0, 0.0, 3.0, 0.0], [0, 0.25, 1, 0.25],
    "3 delta[n-2]: z is 3 times the impulse4 z shifted circularly by 2; the scale cancels")
add("impulse3", [1.0, 0.0, 0.0], [1, 1 / 3, 1 / 3],
    "z = 1, j/sqrt 3, -j/sqrt 3 (ADR 0185): |z|^2 = 1, 1/3, 1/3")
add("constant", [2.0, 2.0, 2.0], [1, 1, 1], "DC only: z = 2 everywhere, 0 dB")
n_, m = 64, 0.5
env = [1 + m * math.cos(2 * math.pi * 2 * n / n_) for n in range(n_)]
add("am_tone", [e * math.cos(2 * math.pi * 10 * n / n_) for n, e in enumerate(env)],
    [(e / (1 + m)) ** 2 for e in env],
    "(1 + 0.5 cos(2 pi 2n/64)) cos(2 pi 10n/64): bins 8, 10, 12 are all positive, so |z| is "
    "exactly the envelope; ETC = 20 log10(env/1.5)", {"abs": 1e-9, "rel": 1e-12})


def err(cid, h, why):
    cases.append({"id": f"energy_time_curve.{cid}", "op": "energy_time_curve",
                  "args": {"impulse_response": h}, "error": "invalid_argument", "source": why})


err("silent", [0.0, 0.0, 0.0], "all zero")
err("empty", [], "empty")
err("nan", [1.0, "nan", 0.5], "not finite")

doc = {
    "schema": 1,
    "suite": "energy_time_curve",
    "description": "Energy-time curve (conventions: Energy-time curve; ADR 0186).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "energy_time_curve.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/energy_time_curve.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
