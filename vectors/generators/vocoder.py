"""Writes vectors/cases/vocoder.json, stdlib only.

Channel vocoder (conventions: Channel vocoder; ADR 0293). Band k is centred at
low (high/low)^((k + 1/2)/bands); each band is (1/q) times the ADR 0279 state-variable
band-pass, run in stdlib floats as in vectors/generators/auto_wah.py; each modulator band's
envelope is the ADR 0238 recurrence in exact rationals, rounded once.

Run from the repo root: python vectors/generators/vocoder.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-10}
cases = []


def band(v, gs, k):
    ic1 = ic2 = 0.0
    out = []
    for x, g in zip(v, gs):
        a1 = 1 / (1 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        out.append(v1)
    return out


def envelope(mags, a, r):
    out, prev = [], Fr(0)
    for m in mags:
        m = Fr(m)
        c = Fr(a) if m > prev else Fr(r)
        prev = m + c * (prev - m)
        out.append(prev)
    return out


def add(cid, c, m, nb, lo, hi, q, a, r, fs, why):
    k = 1 / q
    y = [0.0] * len(c)
    for b in range(nb):
        f = lo * (hi / lo) ** ((b + 0.5) / nb)
        g = [math.tan(math.pi * f / fs)] * len(c)
        cb = [v * k for v in band(c, g, k)]
        mb = [v * k for v in band(m, g, k)]
        e = [float(v) for v in envelope([abs(v) for v in mb], a, r)]
        y = [s + u * w for s, u, w in zip(y, cb, e)]
    cases.append({"id": f"vocoder.{cid}", "op": "vocoder",
                  "args": {"carrier": c, "modulator": m, "bands": nb, "low": lo, "high": hi,
                           "q": q, "attack": a, "release": r, "sample_rate": fs},
                  "expected": y, "tol": TOL, "source": why})
    return y


SAW = [((n * 0.3) % 2.0) - 1.0 for n in range(16)]
V = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("one_band", SAW, V, 1, 0.05, 0.2, 2.0, 0.0, 0.0, 1.0,
    "one band at sqrt(0.05 x 0.2) = 0.1 fs, instant envelope")
add("four_bands", SAW, V, 4, 0.02, 0.4, 4.0, 0.5, 0.9, 1.0, "four bands from 0.02 to 0.4 fs")
add("hz", SAW, V, 3, 200.0, 3200.0, 3.0, 0.2, 0.95, 8000.0, "three bands from 200 to 3200 Hz")
silent = add("silent_modulator", SAW, [0.0] * 16, 4, 0.02, 0.4, 4.0, 0.5, 0.9, 1.0,
             "a silent modulator: zero output")
assert silent == [0.0] * 16


def err(cid, why, **args):
    base = {"carrier": [1.0, 2.0], "modulator": [0.5, 0.5], "bands": 2, "low": 0.5, "high": 2.0,
            "q": 2.0, "attack": 0.5, "release": 0.5, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"vocoder.{cid}", "op": "vocoder", "args": base,
                  "error": "invalid_argument", "source": why})


err("bands_zero", "bands must be at least 1", bands=0)
err("low_above_high", "low must be below high", low=3.0)
err("high_nyquist", "high must be below fs/2", high=4.0)
err("length_mismatch", "carrier and modulator must have the same length", modulator=[1.0])
err("q_zero", "q must be positive", q=0.0)

doc = {
    "schema": 1,
    "suite": "vocoder",
    "description": "Channel vocoder (conventions: Channel vocoder; ADR 0293).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "vocoder.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/vocoder.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
