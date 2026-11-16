"""Writes vectors/cases/mel_filterbank.json, stdlib only.

The edges and the triangle weights are computed in 50-digit decimal from the formulas
(conventions: Mel filterbank; ADR 0155), with the mel scales of ADR 0154 written out again
here. On the Slaney scale below 1 kHz the mel is linear, so the edges fall on whole hundreds
of Hz, and the generator checks the hand-worked rows there.

Run from the repo root: python vectors/generators/mel_filterbank.py [--check]
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
SP = D(200) / 3
STEP = D("6.4").ln() / 27


def to_mel(f, scale):
    if scale == "htk":
        return 2595 * (1 + f / 700).log10()
    return f / SP if f < 1000 else 15 + (f / 1000).ln() / STEP


def to_hz(m, scale):
    if scale == "htk":
        return 700 * (D(10) ** (m / 2595) - 1)
    return m * SP if m < 15 else 1000 * ((m - 15) * STEP).exp()


def bank(n, nfft, fs, lo, hi, scale, area):
    fs, lo, hi = D(fs), D(lo), D(hi)
    m_lo, m_hi = to_mel(lo, scale), to_mel(hi, scale)
    f = [to_hz(m_lo + (m_hi - m_lo) * i / (n + 1), scale) for i in range(n + 2)]
    rows = []
    for i in range(n):
        row = []
        for k in range(nfft // 2 + 1):
            b = k * fs / nfft
            w = max(D(0), min((b - f[i]) / (f[i + 1] - f[i]), (f[i + 2] - b) / (f[i + 2] - f[i + 1])))
            row.append(w * 2 / (f[i + 2] - f[i]) if area else w)
        rows.append(row)
    return rows


def case(cid, n, nfft, fs, lo, hi, scale, area, why, hand=None):
    rows = bank(n, nfft, fs, lo, fs / 2 if hi is None else hi, scale, area)
    for i, want in (hand or {}).items():
        assert all(abs(a - D(b)) < D(10) ** -40 for a, b in zip(rows[i], want)), (cid, i)
    args = {"n_filters": n, "nfft": nfft, "sample_rate": float(fs), "min_frequency": float(lo)}
    if hi is not None:
        args["max_frequency"] = float(hi)
    if scale != "htk":
        args["scale"] = scale
    if area:
        args["area_normalized"] = True
    cases.append({"id": f"mel_filterbank.{cid}", "op": "mel_filterbank", "args": args,
                  "expected": [[float(v) for v in r] for r in rows], "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"n_filters": 4, "nfft": 40, "sample_rate": 4000.0, "min_frequency": 0.0,
            "max_frequency": 1000.0, "scale": "slaney"}
    full.update(args)
    cases.append({"id": f"mel_filterbank.{cid}", "op": "mel_filterbank", "args": full,
                  "error": "invalid_argument", "source": why})


Z = [0] * 21
TRI0 = ["0", "0.5", "1", "0.5"] + ["0"] * 17
TRI3 = ["0"] * 6 + ["0", "0.5", "1", "0.5", "0"] + ["0"] * 10
LIN = ("Slaney below 1 kHz is linear: 0..15 mel in 5 steps of 3 mel = 200 Hz, so the edges are "
       "0, 200, ..., 1000 Hz; 100 Hz bins (fs 4000, nfft 40)")
case("slaney_linear", 4, 40, 4000, 0, 1000, "slaney", False,
     LIN + "; filter 0 is 0, 1/2, 1, 1/2, 0 at 0..400 Hz", {0: TRI0, 3: TRI3})
case("slaney_linear_area", 4, 40, 4000, 0, 1000, "slaney", True,
     LIN + "; area normalized: times 2/400, so the peak is 1/200",
     {0: [str(D(v) / 200) for v in TRI0]})
case("nonzero_min", 3, 40, 4000, 200, 1000, "slaney", False,
     "Slaney linear, 3..15 mel in 4 steps of 3 mel: edges 200, 400, ..., 1000 Hz; 100 Hz bins",
     {0: ["0", "0", "0", "0.5", "1", "0.5"] + ["0"] * 15})
case("htk", 2, 16, 16000, 0, 6300, "htk", False,
     "HTK 0..2595 mel in 3 steps, edges 700 (10^(k/3) - 1) Hz; weights at 1000 Hz bins, in decimal")
case("slaney_log", 2, 32, 16000, 1000, 6400, "slaney", False,
     "Slaney log region, 15..42 mel in 3 steps of 9 mel: edges 1000 * 6.4^(k/3) Hz; 500 Hz bins, "
     "in decimal")
case("default_max", 3, 8, 8000, 0, None, "htk", False,
     "max_frequency defaults to fs/2 = 4000 Hz; HTK edges and weights in decimal")
case("empty_filters", 4, 4, 4000, 0, 1000, "slaney", False,
     "edges every 200 Hz but bins every 1000 Hz: each bin sits on an edge or outside, so every "
     "weight is 0", {i: ["0"] * 3 for i in range(4)})

err("no_filters", {"n_filters": 0}, "n_filters must be at least 1")
err("nfft_one", {"nfft": 1}, "nfft must be at least 2")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("max_above_nyquist", {"max_frequency": 2000.5}, "max_frequency must not exceed fs/2 = 2000")
err("min_at_max", {"min_frequency": 1000.0}, "min_frequency must be below max_frequency")
err("negative_min", {"min_frequency": -1.0}, "min_frequency must be at least 0")
err("nan_min", {"min_frequency": "nan"}, "min_frequency must be finite")
err("bad_scale", {"scale": "bark"}, 'scale must be "htk" or "slaney"')

doc = {
    "schema": 1,
    "suite": "mel_filterbank",
    "description": "Mel filterbank (conventions: Mel filterbank; ADR 0155).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mel_filterbank.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mel_filterbank.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
