"""Writes vectors/cases/two_tone_imd.json by hand, using only the Python standard library.

The inputs are two coherent tones through a cubic nonlinearity; the expected tone and product
powers are its trigonometric expansion worked by hand (conventions: Two-tone intermodulation;
ADR 0107). For y = x + a3*x^3 on A1 cos w1 n + A2 cos w2 n the tone at w1 has amplitude
A1 + a3*(3/4 A1^3 + 3/2 A1 A2^2) and the product at 2w1 - w2 has (3/4) a3 A1^2 A2; for complex
y = x + a3*|x|^2 x on A(e^{jw1 n} + e^{jw2 n}) the tones have A(1 + 3 a3 A^2) and the products
a3 A^3. The tones are coherent and the 4-term Blackman-Harris window leaks only three bins, so
each group holds its line's whole power. No other product of the cubic falls near a group.

Run from the repo root: python vectors/generators/two_tone_imd.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

OP = "two_tone_imd"
N = 1024
cases = []


def result(tf, tp, imf, imp):
    pt = (tp[0] + tp[1]) / 2
    dbc = [10 * math.log10(p / pt) for p in imp]
    worst = max(dbc)
    return {"tone_frequencies": tf, "tone_powers": [float(p) for p in tp],
            "imd_frequencies": imf, "imd_powers": [float(p) for p in imp], "imd_dbc": dbc,
            "worst_imd_dbc": worst, "ip3_db": 10 * math.log10(pt) - worst / 2}


def real_case(cid, a1, a2, a3, k1, k2, why):
    w1, w2 = 2 * math.pi * k1 / N, 2 * math.pi * k2 / N
    x = [float(a1) * math.cos(w1 * n) + float(a2) * math.cos(w2 * n) for n in range(N)]
    y = [v + float(a3) * v**3 for v in x]
    t1 = a1 + a3 * (F(3, 4) * a1**3 + F(3, 2) * a1 * a2**2)
    t2 = a2 + a3 * (F(3, 4) * a2**3 + F(3, 2) * a2 * a1**2)
    i1 = F(3, 4) * a3 * a1**2 * a2
    i2 = F(3, 4) * a3 * a2**2 * a1
    lo, hi = 2 * k1 - k2, 2 * k2 - k1
    exp = result([float(k1), float(k2)], [t1**2 / 2, t2**2 / 2],
                 [float(abs(lo)), float(hi if hi <= N / 2 else N - hi)], [i1**2 / 2, i2**2 / 2])
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": y, "sample_rate": float(N), "f1": float(k1),
                           "f2": float(k2)},
                  "expected": exp, "tol": {"abs": 1e-12, "rel": 1e-9}, "source": why})


real_case("equal_tones_cubic", F(1), F(1), F(1, 10), 100, 130,
          "by hand: y = x + 0.1x^3, tones 1.225 (power 0.7503125), products 0.075 (0.0028125)")
real_case("unequal_tones_compressive", F(1), F(1, 2), F(-1, 20), 200, 260,
          "by hand: y = x - 0.05x^3 on cos + 0.5 cos: products (3/4)a3 A1^2 A2 and A1 A2^2")

# complex: A(e^{jw1 n} + e^{jw2 n}) with A = 1/2, a3 = 1/5, f1 = -100, f2 = 130 bins
A, a3, k1, k2 = F(1, 2), F(1, 5), -100, 130
re, im = [], []
for n in range(N):
    z = float(A) * (complex(math.cos(2 * math.pi * k1 * n / N), math.sin(2 * math.pi * k1 * n / N))
                    + complex(math.cos(2 * math.pi * k2 * n / N),
                              math.sin(2 * math.pi * k2 * n / N)))
    z = z + float(a3) * abs(z) ** 2 * z
    re.append(z.real)
    im.append(z.imag)
tone = A * (1 + 3 * a3 * A**2)
prod = a3 * A**3
cases.append({"id": f"{OP}.complex_cubic", "op": OP,
              "args": {"samples": {"re": re, "im": im}, "sample_rate": float(N), "f1": -100.0,
                       "f2": 130.0},
              "expected": result([-100.0, 130.0], [tone**2, tone**2], [-330.0, 360.0],
                                 [prod**2, prod**2]),
              "tol": {"abs": 1e-12, "rel": 1e-9},
              "source": "by hand: y = x + 0.2|x|^2 x on 0.5(e^{jw1n} + e^{jw2n}): tones 0.575, "
              "products 0.025, at 2f1 - f2 = -330 and 2f2 - f1 = 360"})

M = 128


def tones(*ks):
    return [sum(math.cos(2 * math.pi * k * n / M) for k in ks) for n in range(M)]


for cid, x, f1, f2, why in (
    ("f1_not_below_f2", tones(30, 50), 50.0, 30.0, "f1 must be below f2"),
    ("equal_frequencies", tones(30, 50), 30.0, 30.0, "f1 must be below f2"),
    ("f2_above_nyquist", tones(30, 50), 30.0, 65.0, "f2 must be at most sample_rate/2"),
    ("real_negative_f1", tones(30, 50), -30.0, 50.0, "real input needs f >= 0"),
    ("f1_in_dc_group", tones(3, 50), 3.0, 50.0, "f1 falls in the DC group (half-width 4)"),
    ("f2_in_f1_group", tones(30, 33), 30.0, 33.0, "f2's bin is inside the f1 group"),
    ("no_power_at_f2", tones(30), 30.0, 50.0, "the f2 group has no power"),
    ("product_on_dc", tones(30, 60), 30.0, 60.0, "2f1 - f2 = 0 falls in the DC group"),
    ("product_on_tone", tones(20, 50), 20.0, 50.0,
     "2f2 - f1 = 80 folds to 48, inside the f2 group"),
    ("one_sample", [1.0], 0.1, 0.2, "the spectrum needs at least two samples"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": x, "sample_rate": float(M) if len(x) > 1 else 1.0,
                           "f1": f1, "f2": f2},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Two-tone third-order intermodulation and IP3 (conventions: Two-tone "
    "intermodulation; ADR 0107).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
