"""Writes vectors/cases/cepstrum_pitch.json, stdlib only.

The cepstrum of x = delta + a delta[n-P], |a| < 1, is c_inf[+-kP] = (-1)^(k+1) a^k / (2k)
(the series of ln|1 + a e^(-jPw)|, ADR 0151), aliased at M = nfft bins: c[m] = sum over j of
c_inf[m + jM]. It is summed in Fractions until |a|^k < 2^-300. The peak, the parabola and the
strength then follow the definition (conventions: Cepstrum pitch; ADR 0152) in Fractions, and
are rounded once.

Run from the repo root: python vectors/generators/cepstrum_pitch.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def cepstrum(a, p, m_bins):
    a = F(a)
    c = [F(0)] * m_bins
    k = 1
    while a != 0 and abs(a) ** k >= F(1, 2**300):
        v = (-1) ** (k + 1) * a**k / (2 * k)
        c[(k * p) % m_bins] += v
        c[(-k * p) % m_bins] += v
        k += 1
    return c


def case(cid, samples, a, p, nfft, fs, fmin, fmax, why, *, refined):
    c = cepstrum(a, p, nfft)
    lo, hi = math.ceil(F(fs) / F(fmax)), math.floor(F(fs) / F(fmin))
    assert lo <= hi and 2 * hi < nfft
    best = lo
    for q in range(lo + 1, hi + 1):
        if c[q] > c[best]:
            best = q
    left, peak, right = c[best - 1], c[best], c[best + 1]
    curve = left - 2 * peak + right
    delta = (left - right) / (2 * curve) if peak >= left and peak >= right and curve < 0 else F(0)
    assert (delta != 0) == refined, (cid, best, delta)
    q = best + delta
    cases.append({"id": f"cepstrum_pitch.{cid}", "op": "cepstrum_pitch",
                  "args": {"samples": [float(v) for v in samples], "sample_rate": float(fs),
                           "min_frequency": float(fmin), "max_frequency": float(fmax),
                           "nfft": nfft},
                  "expected": {"frequency": float(F(fs) / q), "quefrency": float(q),
                               "strength": float(peak)},
                  "tol": TOL, "source": why + f"; L = {best}"})


def err(cid, args, why):
    full = {"samples": [1.0, 0.5], "sample_rate": 16.0, "min_frequency": 2.5,
            "max_frequency": 6.0, "nfft": 16}
    full.update(args)
    cases.append({"id": f"cepstrum_pitch.{cid}", "op": "cepstrum_pitch", "args": full,
                  "error": "invalid_argument", "source": why})


S = ("c_inf[+-kP] = (-1)^(k+1) a^k / (2k) from the series of ln|1 + a e^(-jPw)|, aliased at "
     "nfft bins, peak and parabola in Fractions")
case("echo", [1, 0, 0, 0, 0, 0.5], 0.5, 5, 32, 32, 2.5, 8,
     S + "; an echo at P = 5, a = 1/2, quefrencies 4..12: the peak 1/4 at 5 has only tiny "
     "aliased neighbours", refined=True)
case("adjacent", [1, 0.5], 0.5, 1, 16, 16, 2.5, 6,
     S + "; P = 1, a = 1/2, quefrencies 3..6: c3 ~ a^3/6 sits between negative c2 and c4, so "
     "the parabola moves it", refined=True)
case("rising_edge", [1, -0.5], -0.5, 1, 16, 16, 2.5, 6,
     S + "; P = 1, a = -1/2: every c[n] ~ -(1/2)^n / (2n) is negative and rises with n, so the "
     "peak is the edge 6 and c7 > c6 means no parabola", refined=False)
case("impulse_tie", [1], 0, 1, 16, 16, 2.5, 6,
     "x = delta: ln|X| = 0, so c = 0 everywhere; quefrencies 3..6 tie, the smallest wins, the "
     "curvature is 0 so no parabola: q = 3, f = 16/3, strength 0", refined=False)

err("empty_range", {"min_frequency": 5.0, "max_frequency": 5.0},
    "fs/f = 3.2: quefrencies from ceil 4 to floor 3 is empty")
err("second_half", {"min_frequency": 2.0}, "hi = 16/2 = 8, and 2 * 8 is not below nfft = 16")
err("min_above_max", {"min_frequency": 7.0}, "min_frequency must not exceed max_frequency")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("zero_bin", {"samples": [1.0, 1.0, 0.0, 0.0], "min_frequency": 16.0, "max_frequency": 16.0,
                 "nfft": 4}, "X[2] = 1 + e^(-j pi) = 0, and ln 0 is undefined")
err("nfft_short", {"samples": [1.0, 0.5, 0.25], "nfft": 2, "min_frequency": 16.0,
                   "max_frequency": 16.0}, "nfft must be at least N = 3")
err("nan", {"samples": [1.0, "nan"]}, "samples must be finite")

doc = {
    "schema": 1,
    "suite": "cepstrum_pitch",
    "description": "Cepstrum pitch (conventions: Cepstrum pitch; ADR 0152).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cepstrum_pitch.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cepstrum_pitch.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
