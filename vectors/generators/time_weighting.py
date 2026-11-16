"""Writes vectors/cases/time_weighting.json, stdlib only.

The exponential time weighting (conventions: Time weighting; ADR 0166) from its closed form
y[n] = (1 - a) sum_{k <= n} a^(n-k) |x[k]|^2, a = exp(-1/(tau fs)), in 50-digit decimal.

Run from the repo root: python vectors/generators/time_weighting.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def weighted(powers, fs, tau):
    a = (-1 / (D(tau) * D(fs))).exp()
    return [float((1 - a) * sum(a ** (n - k) * powers[k] for k in range(n + 1)))
            for n in range(len(powers))]


def case(cid, samples, fs, tau, why):
    if isinstance(samples, dict):
        powers = [D(r) ** 2 + D(i) ** 2 for r, i in zip(samples["re"], samples["im"])]
    else:
        powers = [D(v) ** 2 for v in samples]
    cases.append({"id": f"time_weighting.{cid}", "op": "time_weighting",
                  "args": {"samples": samples, "sample_rate": fs, "time_constant": tau},
                  "expected": weighted(powers, fs, tau), "tol": TOL, "source": why})


step = weighted([D(1)] * 6, 8.0, 0.125)
e = D(1).exp()
assert all(abs(D(v) - (1 - e ** -(n + 1))) < D(10) ** -15 for n, v in enumerate(step))
case("step_tau_fs_one", [1.0] * 6, 8.0, 0.125, "unit step, tau fs = 1: y[n] = 1 - e^-(n+1)")
case("fast_48k", [0.5, -1.0, 0.25, 2.0, 0.0, -0.75, 1.5], 48000.0, 0.125,
     "Fast (tau = 0.125 s) at 48 kHz: the closed-form sum in decimal")
case("slow_48k", [0.5, -1.0, 0.25, 2.0, 0.0, -0.75, 1.5], 48000.0, 1.0,
     "Slow (tau = 1 s) at 48 kHz: the closed-form sum in decimal")
case("impulse_decay", [2.0, 0.0, 0.0, 0.0], 10.0, 0.05,
     "impulse of power 4, tau fs = 0.5: 4 (1 - a) a^n with a = e^-2")
case("complex", {"re": [3.0, 0.0, 1.0], "im": [4.0, 1.0, -1.0]}, 4.0, 0.5,
     "powers |x|^2 = 25, 1, 2, tau fs = 2: the closed-form sum in decimal")
cases.append({"id": "time_weighting.empty", "op": "time_weighting",
              "args": {"samples": [], "sample_rate": 48000.0, "time_constant": 0.125},
              "expected": [], "tol": TOL, "source": "an empty input gives an empty output"})


def err(cid, change, why):
    args = {"samples": [1.0, 2.0], "sample_rate": 48000.0, "time_constant": 0.125}
    args.update(change)
    cases.append({"id": f"time_weighting.{cid}", "op": "time_weighting", "args": args,
                  "error": "invalid_argument", "source": why})


err("nan_sample", {"samples": [1.0, "nan"]}, "samples must be finite")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("inf_rate", {"sample_rate": "inf"}, "sample_rate must be finite")
err("zero_tau", {"time_constant": 0.0}, "time_constant must be positive")
err("negative_tau", {"time_constant": -1.0}, "time_constant must be positive")
err("nan_tau", {"time_constant": "nan"}, "time_constant must be finite")

doc = {
    "schema": 1,
    "suite": "time_weighting",
    "description": "Exponential time weighting (conventions: Time weighting; ADR 0166).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "time_weighting.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/time_weighting.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
