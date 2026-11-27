"""Writes vectors/cases/noise_compensated_decay.json, stdlib only.

Noise-compensated decay (conventions: Noise-compensated decay; ADR 0183): noise window the last
M = floor(tail N + 1/2) samples, nu their mean |h|^2, E[n] = sum_{k=n}^{N-M-1} (|h[k]|^2 - nu),
10 log10(E[n]/E[0]) for n < N - M, -inf where E[n] <= 0. Every sum is exact in fractions of the
samples as stored, with the logarithm in 50-digit decimal; every E[n] is exactly zero or at least
1e-6 of the sum of |p - nu| it adds up, so float rounding cannot change its sign.

Run from the repo root: python vectors/generators/noise_compensated_decay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as F

getcontext().prec = 50
TOL = {"abs": 1e-9, "rel": 1e-12}
cases = []


def expected(powers, tail):
    n = len(powers)
    m = math.floor(F(tail) * n + F(1, 2))
    assert 1 <= m < n
    nu = sum(powers[n - m:]) / m
    e = []
    acc = F(0)
    size = F(0)
    for k in range(n - m - 1, -1, -1):
        acc += powers[k] - nu
        size += abs(powers[k] - nu)
        assert acc == 0 or abs(acc) > size / 10 ** 6, (k, acc, size)
        e.append(acc)
    e.reverse()
    assert e[0] > 0
    out = []
    for v in e:
        if v <= 0:
            out.append("-inf")
        else:
            r = v / e[0]
            out.append(float(10 * (D(r.numerator) / D(r.denominator)).log10()))
    return out


def add(cid, ir, why, tail=None):
    if isinstance(ir, dict):
        powers = [F(a) ** 2 + F(b) ** 2 for a, b in zip(ir["re"], ir["im"])]
    else:
        powers = [F(a) ** 2 for a in ir]
    args = {"impulse_response": ir}
    if tail is not None:
        args["tail"] = tail
    cases.append({"id": f"noise_compensated_decay.{cid}", "op": "noise_compensated_decay",
                  "args": args, "expected": expected(powers, 0.1 if tail is None else tail),
                  "tol": TOL, "source": why})


add("dyadic", [1.0, 0.5, 0.25, 0.125, 0.0625, -0.0625, 0.0625, -0.0625],
    "N = 8, tail 0.5: M = 4, nu = 1/256; p - nu = 255, 63, 15, 3 (/256); E = 336, 81, 18, 3 "
    "(/256)", tail=0.5)


def lcg(seed, count):
    out = []
    for _ in range(count):
        seed = (1103515245 * seed + 12345) % 2 ** 31
        out.append(seed / 2 ** 31 - 0.5)
    return out


NOISE = lcg(7, 100)
add("noisy", [0.9 ** k + 2e-5 * NOISE[k] for k in range(100)],
    "0.9^k plus LCG noise of amplitude 1e-5 throughout, 100 samples, tail 0.2: M = 20; the "
    "samples as stored, cross terms included, summed exactly", tail=0.2)
add("complex", {"re": [0.5, 0.25, 0.125, 0.0, 0.0625, 0.0],
                "im": [0.5, 0.0, 0.125, 0.0625, 0.0, 0.0625]},
    "N = 6, tail 0.3: M = round(1.8) = 2, nu = 1/256; p - nu = 127, 15, 7, 0 (/256): "
    "E = 149, 22, 7, 0 (/256), the last is -inf", tail=0.3)
add("dip", [1.0, 0.5, 0.0, 0.25, 0.0, 0.125, 0.125, -0.125],
    "N = 8, tail 0.3: M = round(2.4) = 2, nu = 1/64; p - nu = 63, 15, -1, 3, -1, 0 (/64): "
    "E = 79, 16, 1, 2, -1, 0 (/64), the last two are -inf", tail=0.3)


def err(cid, ir, why, tail=None):
    args = {"impulse_response": ir}
    if tail is not None:
        args["tail"] = tail
    cases.append({"id": f"noise_compensated_decay.{cid}", "op": "noise_compensated_decay",
                  "args": args, "error": "invalid_argument", "source": why})


err("below_noise", [0.1, 0.0, 1.0, -1.0], "nu = 1 above every earlier power: E[0] <= 0", tail=0.5)
err("tail_rounds_to_zero", [1.0, 0.5, 0.25, 0.125], "N = 4, tail 0.1: M = round(0.4) = 0")
err("tail_takes_all", [1.0, 0.5, 0.25, 0.125], "N = 4, tail 0.9: M = round(3.6) = 4 = N", tail=0.9)
err("tail_one", [1.0, 0.5, 0.25, 0.125], "tail must be below 1", tail=1.0)
err("tail_zero", [1.0, 0.5, 0.25, 0.125], "tail must be above 0", tail=0.0)
err("empty", [], "empty")
err("nan", [1.0, "nan", 0.5, 0.25], "not finite", tail=0.25)

def scaled(cid, base, k, why):
    """Case ``base`` with the responses times 2**k: the measure is a ratio of energies,
    unchanged by a common scale, and a power of 2 scales every value exactly, so the
    expected value is the base case's."""
    c = next(c for c in cases if c["id"] == "noise_compensated_decay." + base)
    s = 2.0**k

    def times(v):
        if isinstance(v, dict):
            return {part: times(v[part]) for part in ("re", "im")}
        assert all(u * s / s == u for u in v), cid
        return [u * s for u in v]

    args = {name: times(v) if name in ("impulse_response", "reference") else v
            for name, v in c["args"].items()}
    cases.append({**c, "id": "noise_compensated_decay." + cid, "args": args, "source": why})


scaled("huge", "dyadic", 1000,
       "case dyadic times 2^1000: squares of the samples overflow a double, but the "
       "measure is a ratio of energies, so the same value")
scaled("tiny", "dyadic", -1000,
       "case dyadic times 2^-1000: squares of the samples underflow to 0, but the "
       "measure is a ratio of energies, so the same value")
scaled("huge_complex", "complex", 1000,
       "case complex times 2^1000: squares of the samples overflow a double, but the "
       "measure is a ratio of energies, so the same value")
scaled("tiny_complex", "complex", -1000,
       "case complex times 2^-1000: squares of the samples underflow to 0, but the "
       "measure is a ratio of energies, so the same value")


doc = {
    "schema": 1,
    "suite": "noise_compensated_decay",
    "description": "Noise-compensated decay (conventions: Noise-compensated decay; ADR 0183).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "noise_compensated_decay.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/noise_compensated_decay.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
