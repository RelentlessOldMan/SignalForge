"""Writes vectors/cases/mel_scale.json, stdlib only.

Exact points of the HTK and Slaney mel scales (conventions: Mel scale; ADR 0154). HTK is
2595 log10(1 + f/700). Slaney is f / (200/3) below 1000 Hz and 15 + 27 ln(f/1000) / ln 6.4 from
1000 Hz. The points are chosen so that most values are exact: 1 + f/700 a power of ten, or
f/1000 a power of 6.4. The rest are computed in 50-digit decimal.

Run from the repo root: python vectors/generators/mel_scale.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def htk(f):
    return D(2595) * (1 + D(f) / 700).log10()


def slaney(f):
    f = D(f)
    return f / (D(200) / 3) if f < 1000 else 15 + 27 * (f / 1000).ln() / D("6.4").ln()


def both(cid, scale, hz, mel, why):
    want = htk(hz) if scale == "htk" else slaney(hz)
    assert abs(want - D(mel)) < D(10) ** -40, (cid, want)
    for op, arg, value, expected in (("hz_to_mel", "hz", hz, mel), ("mel_to_hz", "mel", mel, hz)):
        args = {arg: float(value)}
        if scale != "htk" or cid.endswith("_named"):
            args["scale"] = scale
        cases.append({"id": f"{op}.{cid}", "op": op, "args": args,
                      "expected": float(D(expected)), "tol": TOL, "source": why})


def err(op, cid, args, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


both("htk_zero", "htk", 0, 0, "log10(1 + 0) = 0")
both("htk_6300", "htk", 6300, 2595, "1 + 6300/700 = 10, log10 10 = 1, times 2595")
both("htk_69300_named", "htk", 69300, 5190, "1 + 69300/700 = 100, log10 100 = 2, times 2595")
both("htk_700", "htk", 700, htk(700), "2595 log10 2, in 50-digit decimal")
both("slaney_zero", "slaney", 0, 0, "linear branch: 0 / (200/3)")
both("slaney_500", "slaney", 500, D("7.5"), "linear branch: 500 / (200/3) = 7.5")
both("slaney_1000", "slaney", 1000, 15, "where the branches meet: 1000 / (200/3) = 15 = 15 + 0")
both("slaney_6400", "slaney", 6400, 42, "log branch: ln(6.4) / (ln 6.4 / 27) = 27, plus 15")
both("slaney_2000", "slaney", 2000, slaney(2000), "log branch: 15 + 27 ln 2 / ln 6.4, in decimal")

for op, arg in (("hz_to_mel", "hz"), ("mel_to_hz", "mel")):
    err(op, "negative", {arg: -1.0}, "values must be non-negative")
    err(op, "nan", {arg: "nan"}, "values must be finite")
    err(op, "inf", {arg: "inf"}, "values must be finite")
    err(op, "bad_scale", {arg: 100.0, "scale": "bark"}, 'scale must be "htk" or "slaney"')

doc = {
    "schema": 1,
    "suite": "mel_scale",
    "description": "Mel scale, HTK and Slaney (conventions: Mel scale; ADR 0154).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mel_scale.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mel_scale.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
