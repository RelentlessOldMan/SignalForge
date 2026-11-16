"""Writes vectors/cases/find_tones.json, stdlib only.

The tones' expected values come from the definition (conventions: Spectra, Find tones;
ADR 0137), worked by hand or analytically:

- A Gaussian `h·exp(−(k − μ)²/2)`, sampled only on its peak bin and that bin's two neighbours,
  is a parabola in dB on those three bins. Its tone is therefore at `μ` with height `h`. Its
  prominence is its peak bin's value minus the floor.
- The plateaus, the tie and the zero neighbour are worked by hand. The linear fit of 0, 1, 1/2
  has its vertex at 7/6 and height 49/48.

Run from the repo root: python vectors/generators/find_tones.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, freqs, psd, count, want, why, **extra):
    args = {"frequencies": freqs, "psd": psd, "count": count, **extra}
    expected = [{"index": i, "frequency": f, "height": h, "prominence": p} for i, f, h, p in want]
    cases.append({"id": f"find_tones.{cid}", "op": "find_tones", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"find_tones.{cid}", "op": "find_tones", "args": args,
                  "error": "invalid_argument", "source": why})


def g(h, mu, k):
    return h * math.exp(-((k - mu) ** 2) / 2)


# Two Gaussians on 10 Hz bins: 8 at 3.2 on bins 2-4, 2 at 8.75 on bins 8-10, 0.1 elsewhere.
FREQS = [10.0 * k for k in range(12)]
PSD = [0.1] * 12
for k in (2, 3, 4):
    PSD[k] = g(8.0, 3.2, k)
for k in (8, 9, 10):
    PSD[k] = g(2.0, 8.75, k)
A = (3, 32.0, 8.0, g(8.0, 3.2, 3) - 0.1)
B = (9, 87.5, 2.0, g(2.0, 8.75, 9) - 0.1)
WHY = ("Gaussians 8 at bin 3.2 and 2 at bin 8.75, sampled on three bins each over a 0.1 floor: "
       "vertices 32 Hz and 87.5 Hz at heights 8 and 2; prominences peak bin minus 0.1")
case("two", FREQS, PSD, 2, [A, B], WHY)
case("one", FREQS, PSD, 1, [A], "count 1 keeps the more prominent; " + WHY)
case("more_than_found", FREQS, PSD, 5, [A, B], "count 5 finds only two; " + WHY)
case("threshold", FREQS, PSD, 5, [A], "min_prominence 3 drops the smaller; " + WHY,
     min_prominence=3.0)

MIXED = [0.0, 1.0, 0.5, 0.2, 3.0, 3.0, 3.0, 0.2, 0.0]
K9 = [float(k) for k in range(9)]
case("grid_in_db", K9, MIXED, 2, [(5, 5.0, 3.0, 3.0), (1, 1.0, 1.0, 0.8)],
     "the plateau of three is flat, and bin 1's left neighbour is 0 in dB: grid values; "
     "prominences 3 and 1 - 0.2")
case("linear", K9, MIXED, 2, [(5, 5.0, 3.0, 3.0), (1, 7 / 6, 49 / 48, 0.8)],
     "on the linear scale bin 1 fits 0, 1, 1/2: vertex 7/6, height 49/48; the plateau stays",
     scale="linear")
case("even_plateau", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [0.0, 1.0, 2.0, 2.0, 1.0, 0.0], 1,
     [(2, 2.5, 2 ** (9 / 8), 2.0)],
     "the run 2, 2 has index 2; dB 0, D, D gives offset 1/2 and height 2^(9/8); prominence 2")
case("tie", [0.0, 1.0, 2.0, 3.0, 4.0], [0.5, 2.0, 0.5, 2.0, 0.5], 1, [(1, 1.0, 2.0, 1.5)],
     "equal prominences 1.5: the lower frequency wins; symmetric, so offset 0")

T = {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, 1.0, 0.0]}
err("count_zero", {**T, "count": 0}, "count must be at least 1")
err("unknown_scale", {**T, "count": 1, "scale": "log"}, 'scale must be "db" or "linear"')
err("negative_floor", {**T, "count": 1, "min_prominence": -1.0}, "min_prominence must be >= 0")
err("negative_psd", {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, -1.0, 0.0], "count": 1},
    "psd must be non-negative")

doc = {
    "schema": 1,
    "suite": "find_tones",
    "description": "Find tones (conventions: Spectra, Find tones; ADR 0137).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "find_tones.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/find_tones.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
