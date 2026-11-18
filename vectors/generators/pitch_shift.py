"""Writes vectors/cases/pitch_shift.json, stdlib only.

Delay-line pitch shifter (conventions: Delay-line pitch shifter; ADR 0302), transcribed from the
rule: t = (1 - ratio)(n / W), phi = t - floor(t), phi_b = (phi + 1/2) - floor(phi + 1/2); taps
at n - W phi and n - W phi_b read with linear interpolation, zero outside the signal; the output
is sin^2(pi phi) A + cos^2(pi phi) B.

Run from the repo root: python vectors/generators/pitch_shift.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def read(x, p):
    i = math.floor(p)
    f = p - i

    def at(k):
        return x[k] if 0 <= k < len(x) else 0.0

    return at(i) * (1 - f) + at(i + 1) * f


def add(cid, x, ratio, w, why):
    y = []
    for n in range(len(x)):
        t = (1 - ratio) * (n / w)
        phi = t - math.floor(t)
        phi_b = (phi + 0.5) - math.floor(phi + 0.5)
        a = read(x, n - w * phi)
        b = read(x, n - w * phi_b)
        y.append(math.sin(math.pi * phi) ** 2 * a + math.cos(math.pi * phi) ** 2 * b)
    cases.append({"id": f"pitch_shift.{cid}", "op": "pitch_shift",
                  "args": {"samples": x, "ratio": ratio, "window": w},
                  "expected": y, "tol": TOL, "source": why})
    return y


RAMP = [float(n) for n in range(24)]
y = add("unity", RAMP, 1.0, 8.0, "ratio 1: the input delayed by W/2 = 4")
assert y == [0.0] * 4 + RAMP[:20]
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0,
     0.7, -0.2, 0.35, -0.85, 0.15, 0.45, -0.55, 1.05]
add("down_octave", M, 0.5, 8.0, "ratio 1/2, window 8: the delay grows half a sample per sample")
add("up_fifth", M, 1.5, 8.0, "ratio 3/2, window 8")
add("up_octave", M, 2.0, 4.0, "ratio 2, window 4")
add("non_dyadic", M, 1.25, 10.0, "ratio 5/4, window 10: a phase that is not a binary fraction")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "ratio": 1.5, "window": 8.0}
    base.update(args)
    cases.append({"id": f"pitch_shift.{cid}", "op": "pitch_shift", "args": base,
                  "error": "invalid_argument", "source": why})


err("ratio_zero", "ratio must be positive", ratio=0.0)
err("window_small", "window must be at least 1", window=0.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "pitch_shift",
    "description": "Delay-line pitch shifter (conventions: Delay-line pitch shifter; ADR 0302).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "pitch_shift.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/pitch_shift.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
