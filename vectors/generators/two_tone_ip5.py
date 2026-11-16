"""Writes vectors/cases/two_tone_ip5.json by hand, using only the Python standard library.

The inputs are two coherent tones through a fifth-order term; the expected tone and product
powers are its expansion worked exactly (conventions: Two-tone intermodulation; ADR 0117). A
signal is a set of complex exponentials e^{j 2 pi k n / N} with rational coefficients, keyed by the
integer bin k; products of signals convolve the keys, a conjugate negates them. For real input
y = x + a5*x^5 on A1 cos w1 n + A2 cos w2 n, and for complex input y = x + a5*|x|^4 x on
A(e^{jw1 n} + e^{jw2 n}), the lines are folded into the spectrum (mod N, and for real input onto
0 .. N/2) and summed coherently. Each claimed group's power is that of the line at its centre; the
generator asserts every other line is at least 8 bins from every claimed group, so the 4-term
Blackman-Harris window's three leaked bins never reach a group's four.

Run from the repo root: python vectors/generators/two_tone_ip5.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

OP = "two_tone_ip5"
N = 1024
W = 4
cases = []


def mul(x, y):
    out = {}
    for k1, c1 in x.items():
        for k2, c2 in y.items():
            out[k1 + k2] = out.get(k1 + k2, F(0)) + c1 * c2
    return out


def add(x, y, scale=F(1)):
    out = dict(x)
    for k, c in y.items():
        out[k] = out.get(k, F(0)) + scale * c
    return out


def conj(x):
    return {-k: c for k, c in x.items()}  # every coefficient here is real


def lines(y, complex_):
    """Bin -> power of the folded spectrum: two-sided (-N/2 .. N/2-1) or one-sided (0 .. N/2)."""
    folded = {}
    for k, c in y.items():
        m = (k + N // 2) % N - N // 2
        folded[m] = folded.get(m, F(0)) + c
    if complex_:
        return {k: c * c for k, c in folded.items() if c != 0}
    out = {}
    for k, c in folded.items():
        if c != 0:  # e^{jk} and e^{-jk} together: a cosine of power 2c^2, c^2 from each side
            out[abs(k)] = out.get(abs(k), F(0)) + c * c
    return out


def alias(k, complex_):
    m = (k + N // 2) % N - N // 2
    return m if complex_ else abs(m)


def result(spec, groups, complex_):
    for k in spec:
        if k in groups:
            continue
        for g in groups:
            d = min(abs(k - g), N - abs(k - g)) if complex_ else abs(k - g)
            assert d >= 2 * W, (k, g)
    tp = [spec.get(groups[1], F(0)), spec.get(groups[2], F(0))]
    imp = [spec.get(groups[3], F(0)), spec.get(groups[4], F(0))]
    pt = (tp[0] + tp[1]) / 2
    dbc = [10 * math.log10(p / pt) if p > 0 else "-inf" for p in imp]
    finite = [d for d in dbc if d != "-inf"]
    worst = max(finite) if finite else "-inf"
    ip5 = 10 * math.log10(pt) - worst / 4 if finite else "inf"
    return {"tone_frequencies": [float(groups[1]), float(groups[2])],
            "tone_powers": [float(p) for p in tp],
            "imd_frequencies": [float(groups[3]), float(groups[4])],
            "imd_powers": [float(p) for p in imp], "imd_dbc": dbc,
            "worst_imd_dbc": worst, "ip5_db": ip5}


def real_case(cid, a1, a2, a5, k1, k2, why):
    x = {k1: a1 / 2, -k1: a1 / 2, k2: a2 / 2, -k2: a2 / 2}
    x5 = mul(mul(mul(mul(x, x), x), x), x)
    spec = lines(add(x, x5, a5), False)
    groups = [0, k1, k2, alias(3 * k1 - 2 * k2, False), alias(3 * k2 - 2 * k1, False)]
    samples = [float(a1) * math.cos(2 * math.pi * k1 * n / N)
               + float(a2) * math.cos(2 * math.pi * k2 * n / N) for n in range(N)]
    samples = [v + float(a5) * v**5 for v in samples]
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": samples, "sample_rate": float(N), "f1": float(k1),
                           "f2": float(k2)},
                  "expected": result(spec, groups, False),
                  "tol": {"abs": 1e-12, "rel": 1e-9}, "source": why})


def complex_case(cid, a, a5, k1, k2, why):
    x = {k1: a, k2: a}
    xx = mul(x, conj(x))
    y = add(x, mul(mul(xx, xx), x), a5)
    spec = lines(y, True)
    groups = [0, k1, k2, alias(3 * k1 - 2 * k2, True), alias(3 * k2 - 2 * k1, True)]
    re, im = [], []
    for n in range(N):
        z = float(a) * (complex(math.cos(2 * math.pi * k1 * n / N), math.sin(2 * math.pi * k1 * n / N))
                        + complex(math.cos(2 * math.pi * k2 * n / N),
                                  math.sin(2 * math.pi * k2 * n / N)))
        z = z + float(a5) * abs(z) ** 4 * z
        re.append(z.real)
        im.append(z.imag)
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": {"re": re, "im": im}, "sample_rate": float(N),
                           "f1": float(k1), "f2": float(k2)},
                  "expected": result(spec, groups, True),
                  "tol": {"abs": 1e-12, "rel": 1e-9}, "source": why})


real_case("equal_tones_quintic", F(1), F(1), F(1, 100), 100, 110,
          "by hand: y = x + 0.01x^5 on cos + cos at 100 and 110 bins: products (5/8)(0.01) at 80 "
          "and 130; third-order products at 90 and 120, ten bins from every group")
real_case("unequal_tones_folded_product", F(1), F(1, 2), F(-1, 50), 400, 470,
          "by hand: y = x - 0.02x^5 on cos + 0.5 cos at 400 and 470 bins: lower product 260, "
          "upper 610 folded to 414, coefficients (5/8)a5 A1^3 A2^2 and (5/8)a5 A1^2 A2^3")
real_case("linear_no_products", F(1), F(1), F(0), 100, 110,
          "by hand: y = x; neither product has power, so ip5 is +inf")
complex_case("complex_envelope_quintic", F(1, 2), F(1, 5), -40, 60,
             "by hand: y = x + 0.2|x|^4 x on 0.5(e^{jw1 n} + e^{jw2 n}) at -40 and 60 bins: "
             "fifth-order lines a5 A^5 at -240 and 260, third-order 5 a5 A^5 at -140 and 160")

M = 128


def tones(*ks):
    return [sum(math.cos(2 * math.pi * k * n / M) for k in ks) for n in range(M)]


for cid, x, f1, f2, why in (
    ("f1_not_below_f2", tones(30, 50), 50.0, 30.0, "f1 must be below f2"),
    ("f2_above_nyquist", tones(30, 50), 30.0, 65.0, "f2 must be at most sample_rate/2"),
    ("no_power_at_f2", tones(30), 30.0, 50.0, "the f2 group has no power"),
    ("lower_product_on_dc", tones(20, 30), 20.0, 30.0, "3f1 - 2f2 = 0 falls on the DC group"),
    ("upper_product_folds_on_f2", tones(36, 50), 36.0, 50.0,
     "3f2 - 2f1 = 78 folds to 50, the f2 group"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": x, "sample_rate": float(M), "f1": f1, "f2": f2},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Two-tone fifth-order intermodulation and IP5 (conventions: Two-tone "
    "intermodulation; ADR 0117).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"
lines_ = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines_ + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
