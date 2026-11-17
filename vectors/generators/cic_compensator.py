"""Writes vectors/cases/cic_compensator.json, stdlib only.

CIC droop compensator (conventions: CIC droop compensator; ADR 0232). The droop
A(f) = |sin(pi M f) / (R M sin(pi f / R))|^N comes from the closed form and is cross-checked
against the DTFT of the integer CIC taps at f / R. The taps are the type-1 frequency-sampling sum
h[n] = (D_0 + 2 sum_j D_j cos(2 pi j (n - c) / T)) / T, and the designed response at each grid
frequency j / T is checked to equal D_j.

Run from the repo root: python vectors/generators/cic_compensator.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def cic(r, n, m):
    h = [1]
    for _ in range(n):
        nxt = [0] * (len(h) + r * m - 1)
        for i, v in enumerate(h):
            for j in range(r * m):
                nxt[i + j] += v
        h = nxt
    return h


def droop(r, n, m, f):
    if f == 0:
        return 1.0
    return abs(math.sin(math.pi * m * f) / (r * m * math.sin(math.pi * f / r))) ** n


def design(r, n, m, t, cutoff, fs):
    c = (t - 1) // 2
    d = [1.0 / droop(r, n, m, j / t) if j / t <= cutoff / fs else 0.0 for j in range(c + 1)]
    h = [(d[0] + 2 * sum(d[j] * math.cos(2 * math.pi * j * (i - c) / t) for j in range(1, c + 1)))
         / t for i in range(t)]
    return d, h


def add(cid, r, n, m, t, cutoff, fs, why):
    taps = cic(r, n, m)
    d, h = design(r, n, m, t, cutoff, fs)
    c = (t - 1) // 2
    for j in range(c + 1):
        f = j / t
        dtft = abs(sum(v * cmath.exp(-2j * math.pi * f / r * k) for k, v in enumerate(taps)))
        assert abs(dtft / (r * m) ** n - droop(r, n, m, f)) < 1e-12, (cid, j)
        resp = sum(h[k] * cmath.exp(-2j * math.pi * f * (k - c)) for k in range(t))
        assert abs(resp - d[j]) < 1e-11 * max(1.0, d[j]), (cid, j)
    args = {"factor": r, "stages": n, "num_taps": t, "cutoff": cutoff, "sample_rate": fs}
    if m != 1:
        args["delay"] = m
    cases.append({"id": f"cic_compensator.{cid}", "op": "cic_compensator", "args": args,
                  "expected": h, "tol": TOL, "source": why})
    return h


add("typical", 8, 4, 1, 21, 0.2, 1.0, "R = 8, N = 4, 21 taps, cutoff 0.2 fs")
add("full_band", 16, 3, 1, 15, 0.5, 1.0, "cutoff at fs/2: every grid point compensated")
add("delay_two", 4, 2, 2, 11, 0.25, 1.0, "M = 2, cutoff fs/(2M)")
add("hz_units", 10, 5, 1, 31, 12000.0, 48000.0, "48 kHz low rate, 12 kHz passband")
h = add("no_droop", 1, 3, 1, 9, 0.5, 1.0, "R = M = 1: no droop, so a unit impulse at the centre")
assert all(abs(v - (1.0 if i == 4 else 0.0)) < 1e-15 for i, v in enumerate(h))
h = add("one_tap", 8, 4, 1, 1, 0.3, 1.0, "one tap: D_0 = 1")
assert h == [1.0]


def err(cid, why, **args):
    base = {"factor": 8, "stages": 4, "num_taps": 21, "cutoff": 0.2, "sample_rate": 1.0}
    base.update(args)
    cases.append({"id": f"cic_compensator.{cid}", "op": "cic_compensator", "args": base,
                  "error": "invalid_argument", "source": why})


err("even_taps", "num_taps must be odd", num_taps=20)
err("cutoff_zero", "cutoff must be positive", cutoff=0.0)
err("cutoff_too_high", "cutoff over sample_rate/(2M)", cutoff=0.3, delay=2)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("stages_too_many", "stages must be at most 64", stages=65)

doc = {
    "schema": 1,
    "suite": "cic_compensator",
    "description": "CIC droop compensator (conventions: CIC droop compensator; ADR 0232).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cic_compensator.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cic_compensator.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
