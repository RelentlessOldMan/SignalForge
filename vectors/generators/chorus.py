"""Writes vectors/cases/chorus.json, stdlib only.

Chorus (conventions: Chorus; ADR 0273): the mean of V vibratos (ADR 0271) with LFO phases
(2 pi k)/V, mixed with the dry signal, transcribed with the stdlib math.cos and math.floor.

Run from the repo root: python vectors/generators/chorus.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def voice(x, delay, depth, rate, fs, phase):
    w = 2.0 * math.pi * rate
    v = []
    for n in range(len(x)):
        p = n - (delay + depth * math.cos(w * (n / fs) + phase))
        i = math.floor(p)
        f = p - i
        lo = complex(x[i]) if i >= 0 else 0j
        hi = complex(x[i + 1]) if i + 1 >= 0 and f > 0 else 0j
        v.append(complex(lo.real * (1 - f) + hi.real * f, lo.imag * (1 - f) + hi.imag * f))
    return v


def run(x, delay, depth, rate, fs, voices, mix):
    total = voice(x, delay, depth, rate, fs, 0.0)
    for k in range(1, voices):
        v = voice(x, delay, depth, rate, fs, 2.0 * math.pi * k / voices)
        total = [complex(a.real + b.real, a.imag + b.imag) for a, b in zip(total, v)]
    y = []
    for xn, t in zip(x, total):
        xc = complex(xn)
        wr, wi = t.real / voices, t.imag / voices
        y.append(complex(xc.real * (1 - mix) + wr * mix, xc.imag * (1 - mix) + wi * mix))
    return y


def add(cid, x, delay, depth, rate, fs, voices, mix, why):
    y = [v.real for v in run(x, delay, depth, rate, fs, voices, mix)]
    cases.append({"id": f"chorus.{cid}", "op": "chorus",
                  "args": {"samples": x, "delay": delay, "depth": depth, "rate": rate,
                           "sample_rate": fs, "voices": voices, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [1.0, -0.5, 0.25, 2.0, -1.0, 0.75, 0.5, -0.25]
y = add("fixed", X, 2.0, 0.0, 1.0, 8.0, 4, 0.5,
        "depth 0: every voice is x[n-2], so (x[n] + x[n-2])/2")
assert y == [(a + b) / 2 for a, b in zip(X, [0.0, 0.0] + X[:-2])]
y = add("two_voices_quarter", X, 2.0, 1.0, 2.0, 8.0, 2, 1.0,
        "rate fs/4, two voices half a turn apart: delays 3 and 1, then 2 and 2, ...")
add("three_voices", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05],
    3.25, 1.5, 0.7, 10.0, 3, 0.6, "delay 3.25, depth 1.5, rate 0.7 Hz at 10 Hz, 3 voices, mix 0.6")
add("one_voice", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2], 2.5, 1.0, 1.25, 10.0, 1, 0.3,
    "one voice: the flanger")

cre, cim = [1.0, 0.0, -2.0, 0.5, 0.25], [0.0, 1.0, 0.5, -1.0, 2.0]
yc = run([complex(r, i) for r, i in zip(cre, cim)], 2.0, 1.0, 1.0, 5.0, 2, 0.5)
cases.append({"id": "chorus.complex", "op": "chorus",
              "args": {"samples": {"re": cre, "im": cim}, "delay": 2.0, "depth": 1.0,
                       "rate": 1.0, "sample_rate": 5.0, "voices": 2, "mix": 0.5},
              "expected": {"re": [v.real for v in yc], "im": [v.imag for v in yc]},
              "tol": TOL, "source": "complex, two voices"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 2.0, "depth": 1.0, "rate": 1.0, "sample_rate": 8.0,
            "voices": 3, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"chorus.{cid}", "op": "chorus", "args": base,
                  "error": "invalid_argument", "source": why})


err("voices_zero", "voices must be at least 1", voices=0)
err("mix_high", "mix must be at most 1", mix=1.25)
err("depth_above_delay", "depth must be at most delay", depth=3.0)
err("fs_zero", "sample_rate must be positive", sample_rate=0.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "chorus",
    "description": "Chorus (conventions: Chorus; ADR 0273).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chorus.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chorus.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
