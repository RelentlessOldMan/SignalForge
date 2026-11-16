"""Writes vectors/cases/speech_transmission_index.json, stdlib only.

Speech transmission index (conventions: Speech transmission index; ADR 0177): TI = (clip(10
log10(m/(1 - m)), -15, 15) + 15)/30 (m <= 0: 0, m >= 1: 1), MTI the row mean, STI = sum alpha_k
MTI_k - sum beta_k sqrt(MTI_k MTI_k+1), with the IEC 60268-16:2020 Table A.1 male weights, in
50-digit decimal.

Run from the repo root: python vectors/generators/speech_transmission_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-14, "rel": 1e-13}
ALPHA = [D(v) for v in ("0.085", "0.127", "0.230", "0.233", "0.309", "0.224", "0.173")]
BETA = [D(v) for v in ("0.085", "0.078", "0.065", "0.011", "0.047", "0.095")]
assert sum(ALPHA) - sum(BETA) == 1
cases = []


def ti(m):
    m = D(m)
    if m <= 0:
        return D(0)
    if m >= 1:
        return D(1)
    snr = min(max(10 * (m / (1 - m)).log10(), D(-15)), D(15))
    return (snr + 15) / 30


def sti(mtf):
    mti = [sum(ti(v) for v in row) / len(row) for row in mtf]
    return (sum(a * t for a, t in zip(ALPHA, mti))
            - sum(b * (mti[k] * mti[k + 1]).sqrt() for k, b in enumerate(BETA)))


def add(cid, mtf, why, expected=None):
    got = sti(mtf)
    if expected is not None:
        assert abs(got - D(expected)) < D(10) ** -40, (cid, got)
    cases.append({"id": f"speech_transmission_index.{cid}", "op": "speech_transmission_index",
                  "args": {"mtf": mtf}, "expected": float(got), "tol": TOL, "source": why})


add("perfect", [[1.0] * 14] * 7, "every m = 1: TI 1, STI = sum alpha - sum beta = 1", 1)
add("silent", [[0.0] * 14] * 7, "every m = 0: STI 0", 0)
add("uniform_half", [[0.5] * 14] * 7, "m = 0.5: SNR 0, TI 0.5; uniform, so STI = TI", "0.5")
add("uniform_point_nine", [[0.9] * 14] * 7,
    "m = 0.9: SNR = 10 log10 9, TI = (10 log10 9 + 15)/30; uniform, so STI = TI")
add("low_bands_only", [[1.0] * 14] * 3 + [[0.0] * 14] * 4,
    "MTI = 1, 1, 1, 0, 0, 0, 0: 0.085 + 0.127 + 0.230 - 0.085 - 0.078 = 0.279", "0.279")
add("mixed_columns", [[1.0] * 7 + [0.0] * 7] * 7,
    "each row half 1, half 0: every MTI 0.5, so STI = 0.5", "0.5")
add("clipping", [[1.5, -0.2]] * 7, "m = 1.5 clips to TI 1, m = -0.2 to TI 0: MTI 0.5, STI 0.5",
    "0.5")
add("snr_clip", [[0.999] * 2, [0.001] * 2] + [[0.5] * 2] * 5,
    "m = 0.999: SNR 30 dB clips to 15 (TI 1); m = 0.001 clips to -15 (TI 0); the rest TI 0.5")
add("stipa_shape", [[0.8, 0.6], [0.7, 0.5], [0.9, 0.3], [0.6, 0.6], [0.75, 0.55], [0.4, 0.85],
                    [0.5, 0.65]], "a 7 x 2 matrix, as STIPA measures: the formula by hand")


def err(cid, mtf, why):
    cases.append({"id": f"speech_transmission_index.{cid}", "op": "speech_transmission_index",
                  "args": {"mtf": mtf}, "error": "invalid_argument", "source": why})


err("six_rows", [[0.5] * 14] * 6, "mtf must have 7 rows")
err("no_columns", [[]] * 7, "mtf must have at least one column")
err("nan", [[0.5, "nan"]] + [[0.5, 0.5]] * 6, "mtf must be finite")

doc = {
    "schema": 1,
    "suite": "speech_transmission_index",
    "description": "Speech transmission index (conventions: Speech transmission index; ADR 0177).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "speech_transmission_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/speech_transmission_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
