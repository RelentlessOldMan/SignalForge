"""Writes vectors/cases/amplifier.json by hand arithmetic, using only the Python standard library.

It does not import NumPy or SignalForge. Each expected sample is the model's formula at that
sample's amplitude r = |x| (conventions: Channel, Amplifier models; ADR 0114):
Saleh y = x aa/(1 + ba r^2) e^{j ap r^2/(1 + bp r^2)}; Rapp, with u = g r/A_sat,
y = x g/(1 + u^(2p))^(1/(2p)) for u <= 1 and (x/r) A_sat/(1 + u^(-2p))^(1/(2p)) above.

Run from the repo root: python vectors/generators/amplifier.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}


def cx(values):
    return {"re": [complex(v).real for v in values], "im": [complex(v).imag for v in values]}


def saleh(x, aa, ba, ap, bp):
    r2 = abs(x) ** 2
    return x * (aa / (1 + ba * r2)) * cmath.exp(1j * (ap * r2 / (1 + bp * r2)))


def rapp(x, g, a_sat, p):
    r = abs(x)
    u = g * r / a_sat
    if u <= 1:
        return x * (g / (1 + u ** (2 * p)) ** (1 / (2 * p)))
    return x / r * (a_sat / (1 + u ** (-2 * p)) ** (1 / (2 * p)))


def s_case(case_id, xs, aa, ba, ap, bp, src):
    return {"id": case_id, "op": "saleh_amplifier",
            "args": {"samples": cx(xs), "alpha_a": aa, "beta_a": ba, "alpha_phi": ap,
                     "beta_phi": bp},
            "expected": cx([saleh(complex(x), aa, ba, ap, bp) for x in xs]), "tol": TOL,
            "source": src}


def r_case(case_id, xs, g, a_sat, p, src):
    return {"id": case_id, "op": "rapp_amplifier",
            "args": {"samples": cx(xs), "gain": g, "saturation": a_sat, "smoothness": p},
            "expected": cx([rapp(complex(x), g, a_sat, p) for x in xs]), "tol": TOL,
            "source": src}


def s_err(case_id, aa, ba, ap, bp, why):
    return {"id": case_id, "op": "saleh_amplifier",
            "args": {"samples": cx([1 + 0j]), "alpha_a": aa, "beta_a": ba, "alpha_phi": ap,
                     "beta_phi": bp},
            "error": "invalid_argument", "source": why}


def r_err(case_id, g, a_sat, p, why):
    return {"id": case_id, "op": "rapp_amplifier",
            "args": {"samples": cx([1 + 0j]), "gain": g, "saturation": a_sat, "smoothness": p},
            "error": "invalid_argument", "source": why}


TWT = (2.1587, 1.1517, 4.0033, 9.1040)  # Saleh's fitted travelling-wave tube values
peak = 1 / math.sqrt(TWT[1])
twt_x = [0j, cmath.rect(0.3, 0.5), cmath.rect(1.0, -2.0), -0.7 + 0j, cmath.rect(peak, 1.1),
         cmath.rect(3.0, 1.0)]
rapp_x = [0j, 0.25 + 0j, 0.5j, cmath.rect(2.0, 0.7), -1e-3 + 0j, 1e300 + 0j]

cases = [
    s_case("saleh_amplifier.travelling_wave_tube", twt_x, *TWT,
           "by hand: y = x aa/(1 + ba r^2) e^{j ap r^2/(1 + bp r^2)} with Saleh's tube values, at "
           "zero, a negative real sample, the output peak r = 1/sqrt(ba) and past it"),
    s_case("saleh_amplifier.am_am_only", [1 + 0j, 1j, 2 + 0j], 2.0, 1.0, 0.0, 0.0,
           "by hand: aa = 2, ba = 1, no phase: 1 -> 1, j -> j, 2 -> 2*2/5 = 0.8"),
    s_case("saleh_amplifier.negative_unbounded_phase", [0.5 + 0j, cmath.rect(2.0, -0.3)],
           1.0, 0.0, -0.8, 0.0,
           "by hand: linear gain 1, phase -0.8 r^2 with no knee"),
    s_case("saleh_amplifier.empty", [], *TWT, "by hand: no samples in, none out"),
    r_case("rapp_amplifier.p1", rapp_x, 2.0, 1.0, 1.0,
           "by hand: g = 2, A_sat = 1, p = 1; u = 0.5, exactly 1 (A = 1/sqrt 2), 4, 0.002 on a "
           "negative real sample, and 2e300 (A = A_sat)"),
    r_case("rapp_amplifier.p_half", rapp_x, 2.0, 1.0, 0.5,
           "by hand: as p1 with p = 0.5, A(u) = A_sat u/(1 + u)"),
    r_case("rapp_amplifier.p3", rapp_x, 2.0, 1.0, 3.0,
           "by hand: as p1 with p = 3, a sharp knee"),
    r_case("rapp_amplifier.unit_gain_low_saturation", [0.1 + 0.1j, 0.3j, 5 + 0j], 1.0, 0.2, 2.0,
           "by hand: g = 1, A_sat = 0.2, p = 2"),
    s_err("saleh_amplifier.alpha_a_zero", 0.0, 1.0, 1.0, 1.0, "alpha_a must be positive"),
    s_err("saleh_amplifier.alpha_a_negative", -1.0, 1.0, 1.0, 1.0, "alpha_a must be positive"),
    s_err("saleh_amplifier.beta_a_negative", 1.0, -0.1, 1.0, 1.0, "beta_a must not be negative"),
    s_err("saleh_amplifier.beta_phi_negative", 1.0, 1.0, 1.0, -1.0,
          "beta_phi must not be negative"),
    s_err("saleh_amplifier.alpha_phi_nan", 1.0, 1.0, "nan", 1.0, "alpha_phi must be finite"),
    s_err("saleh_amplifier.beta_a_inf", 1.0, "inf", 1.0, 1.0, "beta_a must be finite"),
    r_err("rapp_amplifier.gain_zero", 0.0, 1.0, 1.0, "gain must be positive"),
    r_err("rapp_amplifier.saturation_inf", 1.0, "inf", 1.0, "saturation must be finite"),
    r_err("rapp_amplifier.smoothness_zero", 1.0, 1.0, 0.0, "smoothness must be positive"),
    r_err("rapp_amplifier.smoothness_negative", 1.0, 1.0, -2.0, "smoothness must be positive"),
]

doc = {
    "schema": 1,
    "suite": "amplifier",
    "description": "Saleh and Rapp amplifier models (conventions: Channel, Amplifier models; "
                   "ADR 0114).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "amplifier.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/amplifier.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
