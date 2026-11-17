"""Writes vectors/cases/cic_taps.json and vectors/cases/cic_decimate.json, stdlib only.

CIC decimator (conventions: CIC decimator; ADR 0229). The taps are the coefficients of
((1 - z^-RM) / (1 - z^-1))^N expanded with Python integers and checked to sum to (RM)^N. The
decimator's expected outputs come from running the hardware structure in exact arithmetic: N
integrators at the input rate, every R-th sample from n = 0, then N combs of delay M at the low
rate. They are cross-checked against the FIR form sum_m h[m] x[kR - m].

Run from the repo root: python vectors/generators/cic.py [--check]
With --check it writes nothing and exits 1 unless the files match what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-9, "rel": 1e-13}


def taps(r, n, m):
    h = [1]
    for _ in range(n):
        nxt = [0] * (len(h) + r * m - 1)
        for i, v in enumerate(h):
            for j in range(r * m):
                nxt[i + j] += v
        h = nxt
    assert sum(h) == (r * m) ** n and len(h) == n * (r * m - 1) + 1
    return h


def hardware(x, r, n, m):
    s = list(x)
    for _ in range(n):
        acc = 0
        out = []
        for v in s:
            acc += v
            out.append(acc)
        s = out
    s = s[::r]
    for _ in range(n):
        s = [v - (s[k - m] if k >= m else 0) for k, v in enumerate(s)]
    return s


def fir(x, r, n, m):
    h = taps(r, n, m)
    return [sum(h[j] * x[k - j] for j in range(len(h)) if 0 <= k - j < len(x))
            for k in range(0, len(x), r)]


taps_cases = []


def add_taps(cid, r, n, m, why):
    args = {"factor": r, "stages": n}
    if m != 1:
        args["delay"] = m
    taps_cases.append({"id": f"cic_taps.{cid}", "op": "cic_taps", "args": args,
                       "expected": [float(v) for v in taps(r, n, m)], "tol": TOL, "source": why})


assert taps(2, 2, 1) == [1, 2, 1] and taps(3, 2, 1) == [1, 2, 3, 2, 1]
add_taps("one_stage", 4, 1, 1, "one stage: 4 ones")
add_taps("two_stages", 3, 2, 1, "R = 3, N = 2: the triangle 1 2 3 2 1")
add_taps("delay_two", 2, 3, 2, "R = 2, M = 2, N = 3: (1 + z^-1 + z^-2 + z^-3)^3")
add_taps("five_stages", 5, 5, 1, "R = 5, N = 5: sum 5^5 = 3125")
add_taps("factor_one", 1, 7, 1, "R = M = 1: the single tap 1")
add_taps("at_limit", 2, 53, 1, "(RM)^N = 2^53 exactly: allowed")


def err(store, op, cid, why, **args):
    store.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err(taps_cases, "cic_taps", "factor_zero", "factor must be at least 1", factor=0, stages=2)
err(taps_cases, "cic_taps", "stages_zero", "stages must be at least 1", factor=2, stages=0)
err(taps_cases, "cic_taps", "delay_zero", "delay must be at least 1", factor=2, stages=2, delay=0)
err(taps_cases, "cic_taps", "gain_too_big", "(RM)^N = 2^54 is over 2^53", factor=2, stages=54)
err(taps_cases, "cic_taps", "too_many_stages", "stages must be at most 64", factor=1, stages=65)

dec_cases = []


def add_dec(cid, x, r, n, m, why, cplx=None):
    re = hardware(x, r, n, m)
    assert re == fir(x, r, n, m), cid
    im = hardware(cplx, r, n, m) if cplx is not None else [0] * len(re)
    if cplx is not None:
        assert im == fir(cplx, r, n, m), cid
    samples = ({"re": [float(v) for v in x], "im": [float(v) for v in cplx]} if cplx is not None
               else [float(v) for v in x])
    args = {"samples": samples, "factor": r, "stages": n}
    if m != 1:
        args["delay"] = m
    expected = ({"re": [float(v) for v in re], "im": [float(v) for v in im]} if cplx is not None
                else [float(v) for v in re])
    dec_cases.append({"id": f"cic_decimate.{cid}", "op": "cic_decimate", "args": args,
                      "expected": expected, "tol": TOL, "source": why})
    return re


out = add_dec("dc", [1] * 24, 4, 3, 1, "all ones: the gain (RM)^N = 64 once settled")
assert out[-1] == 64
out = add_dec("impulse", [1] + [0] * 19, 2, 3, 1, "impulse: every other tap")
assert out == taps(2, 3, 1)[::2] + [0] * (10 - len(taps(2, 3, 1)[::2]))
add_dec("integers", [3, -1, 4, 1, -5, 9, 2, -6, 5, 3, -5, 8, 9, -7, 9, 3, 2, -3, 8, 4, -6], 3, 2,
        2, "integer data, R = 3, N = 2, M = 2: exact")
add_dec("fractions", [Fr(1, 2), Fr(-3, 4), Fr(5, 8), Fr(1, 16), Fr(-1), Fr(3, 2), Fr(7, 4)], 2, 4,
        1, "binary fractions, R = 2, N = 4", )
add_dec("ragged_end", [1, 2, 3, 4, 5, 6, 7], 3, 1, 1, "length 7, R = 3: ceil(7/3) = 3 outputs")
add_dec("factor_one", [2, -1, 3, 0, 1], 1, 2, 3, "R = 1, M = 3: plain filtering")
add_dec("complex", [1, 0, -2, 3, 1, -1, 2, 0], 2, 2, 1, "complex samples",
        cplx=[0, 1, 1, -1, 2, 0, -3, 1])
err(dec_cases, "cic_decimate", "empty", "samples must not be empty", samples=[], factor=2,
    stages=2)
err(dec_cases, "cic_decimate", "nan_sample", "samples must be finite", samples=[1.0, "nan"],
    factor=2, stages=2)
err(dec_cases, "cic_decimate", "factor_zero", "factor must be at least 1", samples=[1.0],
    factor=0, stages=2)
err(dec_cases, "cic_decimate", "gain_too_big", "(RM)^N over 2^53", samples=[1.0], factor=1000,
    stages=6)

check = "--check" in sys.argv[1:]
for name, suite, cases in (("cic_taps", "cic_taps", taps_cases),
                           ("cic_decimate", "cic_decimate", dec_cases)):
    doc = {"schema": 1, "suite": suite,
           "description": "CIC decimator (conventions: CIC decimator; ADR 0229).", "cases": cases}
    out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{name}.json"
    lines = ",\n".join("    " + json.dumps(c) for c in cases)
    head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
    text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
    if check:
        if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
            sys.exit(f"{out} is out of date: run python vectors/generators/cic.py")
        print(f"{out} is up to date")
        continue
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(cases)} cases)")
