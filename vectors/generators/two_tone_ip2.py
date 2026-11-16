"""Writes vectors/cases/two_tone_ip2.json by hand, using only the Python standard library.

The inputs are two coherent tones through a square-law term; the expected tone and product
powers are its trigonometric expansion worked by hand (conventions: Two-tone intermodulation;
ADR 0110). For y = x + a2*x^2 on A1 cos w1 n + A2 cos w2 n the tones are untouched and the
products at w2 - w1 and w1 + w2 both have amplitude a2 A1 A2; the square also puts
a2 (A1^2 + A2^2)/2 at DC and a2 A^2/2 at each second harmonic, all away from the groups. For
complex y = x + a2*|x|^2 on A(e^{jw1 n} + e^{jw2 n}) there are lines a2 A^2 at +-(w2 - w1) and
nothing at the sum. The tones are coherent and the 4-term Blackman-Harris window leaks only
three bins, so each group holds its line's whole power.

Run from the repo root: python vectors/generators/two_tone_ip2.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

OP = "two_tone_ip2"
N = 1024
cases = []


def result(tf, tp, imf, imp):
    pt = (tp[0] + tp[1]) / 2
    dbc = [10 * math.log10(p / pt) if p > 0 else "-inf" for p in imp]
    worst = max(d for d in dbc if d != "-inf")
    return {"tone_frequencies": tf, "tone_powers": [float(p) for p in tp],
            "imd_frequencies": imf, "imd_powers": [float(p) for p in imp], "imd_dbc": dbc,
            "worst_imd_dbc": worst, "ip2_db": 10 * math.log10(pt) - worst}


def real_case(cid, a1, a2, sq, k1, k2, why):
    w1, w2 = 2 * math.pi * k1 / N, 2 * math.pi * k2 / N
    x = [float(a1) * math.cos(w1 * n) + float(a2) * math.cos(w2 * n) for n in range(N)]
    y = [v + float(sq) * v**2 for v in x]
    s = k1 + k2
    prod = sq * a1 * a2
    exp = result([float(k1), float(k2)], [a1**2 / 2, a2**2 / 2],
                 [float(k2 - k1), float(s if s <= N / 2 else N - s)], [prod**2 / 2, prod**2 / 2])
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": y, "sample_rate": float(N), "f1": float(k1),
                           "f2": float(k2)},
                  "expected": exp, "tol": {"abs": 1e-12, "rel": 1e-9}, "source": why})


real_case("equal_tones_square", F(1), F(1), F(1, 10), 100, 130,
          "by hand: y = x + 0.1x^2, products 0.1 at 30 and 230 (power 0.005); DC, 200, 260 away")
real_case("unequal_tones_folded_sum", F(1), F(1, 2), F(-1, 20), 260, 300,
          "by hand: y = x - 0.05x^2 on cos + 0.5 cos: products a2 A1 A2 = -0.025 at 40 and "
          "560, folded to 464; harmonics 520 -> 504 and 600 -> 424 away")

# complex: A(e^{jw1 n} + e^{jw2 n}) with A = 1/2, a2 = 1/5, f1 = -100, f2 = 130 bins
A, a2 = F(1, 2), F(1, 5)
re, im = [], []
for n in range(N):
    z = float(A) * (complex(math.cos(2 * math.pi * -100 * n / N), math.sin(2 * math.pi * -100 * n / N))
                    + complex(math.cos(2 * math.pi * 130 * n / N),
                              math.sin(2 * math.pi * 130 * n / N)))
    z = z + float(a2) * abs(z) ** 2
    re.append(z.real)
    im.append(z.imag)
line = a2 * A**2
cases.append({"id": f"{OP}.complex_envelope_square", "op": OP,
              "args": {"samples": {"re": re, "im": im}, "sample_rate": float(N), "f1": -100.0,
                       "f2": 130.0},
              "expected": result([-100.0, 130.0], [A**2, A**2], [230.0, 30.0], [line**2, F(0)]),
              "tol": {"abs": 1e-12, "rel": 1e-9},
              "source": "by hand: y = x + 0.2|x|^2 on 0.5(e^{jw1n} + e^{jw2n}): lines 0.05 at "
              "+-230 and 2 x 0.05 at DC; nothing at the sum 30"})

M = 128


def tones(*ks):
    return [sum(math.cos(2 * math.pi * k * n / M) for k in ks) for n in range(M)]


for cid, x, f1, f2, why in (
    ("f1_not_below_f2", tones(30, 50), 50.0, 30.0, "f1 must be below f2"),
    ("f2_above_nyquist", tones(30, 50), 30.0, 65.0, "f2 must be at most sample_rate/2"),
    ("no_power_at_f2", tones(30), 30.0, 50.0, "the f2 group has no power"),
    ("sum_on_tone", tones(20, 40), 20.0, 40.0, "f2 - f1 = 20 falls on the f1 group"),
    ("sum_folds_on_f2", tones(30, 49), 30.0, 49.0, "f1 + f2 = 79 folds to 49, the f2 group"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": x, "sample_rate": float(M), "f1": f1, "f2": f2},
                  "error": "invalid_argument", "source": why})

# complex tones near -fs/2 and +fs/2: f2 - f1 = 125 wraps to -3, inside the DC group
z = [sum(complex(math.cos(2 * math.pi * k * n / M), math.sin(2 * math.pi * k * n / M))
         for k in (-62, 63)) for n in range(M)]
cases.append({"id": f"{OP}.difference_wraps_onto_dc", "op": OP,
              "args": {"samples": {"re": [v.real for v in z], "im": [v.imag for v in z]},
                       "sample_rate": float(M), "f1": -62.0, "f2": 63.0},
              "error": "invalid_argument",
              "source": "f2 - f1 = 125 wraps to -3 bins, inside the DC group (half-width 4)"})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Two-tone second-order intermodulation and IP2 (conventions: Two-tone "
    "intermodulation; ADR 0110).",
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
