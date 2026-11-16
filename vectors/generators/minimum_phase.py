"""Writes vectors/cases/minimum_phase.json, stdlib only.

Each input is written as g times a product of factors 1 - z z^-1 with real zeros z, and the
generator checks that product against the samples. |1 - z e^(-jw)| = |z| |1 - e^(-jw)/z|, so the
minimum-phase sequence with the same magnitude reflects every zero outside the unit circle to
1/z and scales by |z|, and |g| replaces g (conventions: Minimum phase; ADR 0153). It is
multiplied out in Fractions. The cepstrum aliases at nfft bins with an error near rho^(nfft/2),
where rho is the largest reflected zero radius, and the generator checks that this is below
1e-16.

Run from the repo root: python vectors/generators/minimum_phase.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def multiply(g, zeros):
    p = [F(g)]
    for z in zeros:
        p = [a - F(z) * b for a, b in zip(p + [F(0)], [F(0)] + p)]
    return p


def case(cid, samples, g, zeros, nfft, why):
    assert multiply(g, zeros) == [F(v) for v in samples], cid
    scale, reflected = abs(F(g)), []
    for z in map(F, zeros):
        if abs(z) > 1:
            scale *= abs(z)
            z = 1 / z
        reflected.append(z)
    m = nfft if nfft is not None else max(64, 1 << (8 * len(samples) - 1).bit_length())
    rho = max([abs(z) for z in reflected], default=F(0))
    assert float(rho) ** (m / 2) < 1e-16, cid
    y = multiply(scale, reflected)
    args = {"samples": [float(v) for v in samples]}
    if nfft is not None:
        args["nfft"] = nfft
    cases.append({"id": f"minimum_phase.{cid}", "op": "minimum_phase", "args": args,
                  "expected": [float(v) for v in y] + [0.0] * (m - len(y)), "tol": TOL,
                  "source": why})


def err(cid, args, why):
    cases.append({"id": f"minimum_phase.{cid}", "op": "minimum_phase", "args": args,
                  "error": "invalid_argument", "source": why})


R = "zeros outside the unit circle reflect to 1/z with gain |z|, multiplied out in Fractions"
case("already_minimum", [1, 0.25], 1, [F(-1, 4)], 64,
     "1 + z^-1/4 has its zero at -1/4, inside, so it maps to itself")
case("time_reverse", [0.25, 1], F(1, 4), [-4], 64,
     "1/4 + z^-1 = (1/4)(1 + 4 z^-1): the zero -4 reflects to -1/4 with gain 4, giving 1, 1/4; "
     + R)
case("negative_gain", [-2, -0.5], -2, [F(-1, 4)], 64,
     "-2 (1 + z^-1/4): only |X| is used, so the gain becomes |-2| = 2, giving 2, 1/2")
case("two_zeros", [1, -4.5, 2], 1, [F(1, 2), 4], 128,
     "(1 - z^-1/2)(1 - 4 z^-1): the zero 4 reflects to 1/4 with gain 4, giving "
     "4 (1 - z^-1/2)(1 - z^-1/4) = 4, -3, 1/2; " + R)
case("default_nfft", [0.25, 1], F(1, 4), [-4], None,
     "as time_reverse, with nfft defaulting to the smallest power of two >= max(64, 8 * 2) = 64")
case("odd_nfft", [1, 0.25], 1, [F(-1, 4)], 65,
     "as already_minimum with nfft = 65, which folds c[1..32] and has no middle bin")
case("impulse", [3], 3, [], 4, "3 delta has a flat magnitude 3; its minimum phase is itself")

err("empty", {"samples": []}, "needs at least one sample")
err("nfft_short", {"samples": [1.0, 0.5, 0.25], "nfft": 2}, "nfft must be at least N = 3")
err("zero_bin", {"samples": [1.0, 1.0], "nfft": 2}, "X[1] = 1 - 1 = 0, and ln 0 is undefined")
err("nan", {"samples": [1.0, "nan"]}, "samples must be finite")

doc = {
    "schema": 1,
    "suite": "minimum_phase",
    "description": "Minimum phase from the real cepstrum (conventions: Minimum phase; ADR 0153).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "minimum_phase.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/minimum_phase.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
