"""Writes vectors/cases/schroeder_reverb.json, stdlib only.

Schroeder reverberator (conventions: Schroeder reverberator; ADR 0295). The feedback comb
y[n] = x[n] + g y[n - D] (ADR 0237) and the all-pass y[n] = -g x[n] + x[n - D] + g y[n - D]
(ADR 0240), both zero before the start, run in exact rationals; the mean of the combs feeds the
all-passes in order, the result is rounded once, and the dry/wet blend is stdlib floats.

Run from the repo root: python vectors/generators/schroeder_reverb.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def comb(x, d, g):
    y = []
    for n, v in enumerate(x):
        y.append(v + (g * y[n - d] if n >= d else 0))
    return y


def allpass(x, d, g):
    y = []
    for n, v in enumerate(x):
        y.append(-g * v + (x[n - d] + g * y[n - d] if n >= d else 0))
    return y


def add(cid, x, combs, gains, aps, ag, mix, why):
    fx = [Fr(v) for v in x]
    w = [Fr(0)] * len(x)
    for d, g in zip(combs, gains):
        w = [a + b for a, b in zip(w, comb(fx, d, Fr(g)))]
    w = [v / len(combs) for v in w]
    for d in aps:
        w = allpass(w, d, Fr(ag))
    wet = [float(v) for v in w]
    cases.append({"id": f"schroeder_reverb.{cid}", "op": "schroeder_reverb",
                  "args": {"samples": x, "combs": combs, "comb_gains": gains, "allpasses": aps,
                           "allpass_gain": ag, "mix": mix},
                  "expected": [v * (1 - mix) + u * mix for v, u in zip(x, wet)], "tol": TOL,
                  "source": why})
    return wet


IMP = [1.0] + [0.0] * 29
wet = add("one_comb", IMP, [4], [0.5], [], 0.5, 1.0,
          "one comb, no all-passes: the impulse response 0.5^k at n = 4k")
assert wet == [0.5 ** (n // 4) if n % 4 == 0 else 0.0 for n in range(30)]
add("impulse", IMP, [3, 5, 7], [0.7, 0.6, 0.5], [2, 3], 0.5, 1.0,
    "three combs (3, 5, 7), two all-passes (2, 3): fully wet impulse response")
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("mixed", M, [5, 7, 11, 13], [0.8, -0.75, 0.7, 0.65], [3], -0.6, 0.4,
    "four combs, one all-pass with a negative gain, 40% wet")
add("dry", M, [5], [0.5], [3], 0.5, 0.0, "mix 0: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "combs": [3, 5], "comb_gains": [0.5, 0.5], "allpasses": [2],
            "allpass_gain": 0.5, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"schroeder_reverb.{cid}", "op": "schroeder_reverb", "args": base,
                  "error": "invalid_argument", "source": why})


err("no_combs", "combs must hold at least one delay", combs=[], comb_gains=[])
err("gain_count", "comb_gains must hold one gain per comb", comb_gains=[0.5])
err("comb_gain_one", "a feedback comb needs |gain| < 1", comb_gains=[0.5, 1.0])
err("comb_delay_zero", "comb delays must be at least 1", combs=[0, 5])
err("allpass_gain_one", "the all-pass gain needs |gain| < 1", allpass_gain=-1.0)
err("mix_high", "mix must be at most 1", mix=1.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "schroeder_reverb",
    "description": "Schroeder reverberator (conventions: Schroeder reverberator; ADR 0295).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "schroeder_reverb.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/schroeder_reverb.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
