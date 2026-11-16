"""Writes vectors/cases/real_cepstrum.json, stdlib only.

The cepstra come from the series ln|1 + a e^(-jw)| = sum over n != 0 of
(-1)^(|n|+1) a^|n| / (2|n|) e^(-jnw), for |a| < 1 (conventions: Real cepstrum; ADR 0151).
So x = g (delta + a delta[n-1]) has c_inf[0] = ln|g| and c_inf[n] = (-1)^(|n|+1) a^|n| / (2|n|).
An M-bin cepstrum aliases it: c[m] = sum over j of c_inf[m + jM]. The series is summed in
Fractions until |a|^n < 2^-300, then rounded once; ln|g| is added in floating point. A time
reverse or a delay has the same magnitude spectrum, so the same cepstrum.

Run from the repo root: python vectors/generators/real_cepstrum.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def aliased(a, g, m_bins):
    a = F(a)
    terms = 1
    while abs(a) ** terms >= F(1, 2**300):
        terms += 1
    c = [F(0)] * m_bins
    for n in range(1, terms + m_bins + 1):
        v = (-1) ** (n + 1) * a**n / (2 * n)
        c[n % m_bins] += v  # lag +n
        c[(-n) % m_bins] += v  # lag -n
    out = [float(v) for v in c]
    out[0] = float(c[0]) + math.log(abs(g))
    return out


def case(cid, samples, a, g, nfft, why):
    args = {"samples": [float(v) for v in samples]}
    if nfft is not None:
        args["nfft"] = nfft
    m = len(samples) if nfft is None else nfft
    cases.append({"id": f"real_cepstrum.{cid}", "op": "real_cepstrum", "args": args,
                  "expected": aliased(a, g, m), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"real_cepstrum.{cid}", "op": "real_cepstrum", "args": args,
                  "error": "invalid_argument", "source": why})


S = "c_inf[n] = (-1)^(|n|+1) a^|n| / (2|n|) from the series of ln|1 + a e^(-jw)|, aliased at "
case("minimum_phase", [1, 0.5], 0.5, 1, 8, S + "8 bins; g = 1, a = 1/2")
case("time_reverse", [0.5, 1], 0.5, 1, 8,
     S + "8 bins; the time reverse of 1, 1/2 has the same |X|: 1/2 + e^(-jw) = e^(-jw) "
     "(1 + 1/2 e^(jw)), magnitude |1 + 1/2 e^(-jw)|")
case("delay", [0, 0, 1, 0.5], 0.5, 1, 8, S + "8 bins; a delay leaves |X| unchanged")
case("negative_a_odd_nfft", [1, -0.25], -0.25, 1, 5, S + "5 bins; a = -1/4")
case("gain", [-2, -1], 0.5, -2, 6, S + "6 bins; g = -2 adds ln 2 at quefrency 0")
case("default_nfft", [1, 0.5, 0, 0, 0, 0, 0], 0.5, 1, None,
     S + "7 bins (nfft defaults to N = 7); a = 1/2")
case("impulse", [3], 0, 3, 4, "x = 3 delta: |X| = 3 at every bin, so c = ln 3, 0, 0, 0")

err("empty", {"samples": []}, "needs at least one sample")
err("nfft_short", {"samples": [1.0, 0.5, 0.25], "nfft": 2}, "nfft must be at least N = 3")
err("zero_bin", {"samples": [1.0, 1.0]}, "X[1] = 1 - 1 = 0, and ln 0 is undefined")
err("nan", {"samples": [1.0, "nan"]}, "samples must be finite")

doc = {
    "schema": 1,
    "suite": "real_cepstrum",
    "description": "Real cepstrum (conventions: Real cepstrum; ADR 0151).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "real_cepstrum.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/real_cepstrum.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
