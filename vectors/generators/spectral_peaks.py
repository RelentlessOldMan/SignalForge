"""Writes vectors/cases/spectral_peaks.json, stdlib only.

Each case lists its peaks by hand (conventions: Spectra, Spectral peaks; ADR 0135). The
generator checks each list against a direct reading of the definition. That reading finds the
runs, then takes each base as the minimum over the bins up to the nearest higher one. All values
are small integers or halves, so they are exact.

Run from the repo root: python vectors/generators/spectral_peaks.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def peaks(freqs, x, floor):
    n = len(x)
    runs, start = [], 0
    for k in range(1, n + 1):
        if k == n or x[k] != x[start]:
            runs.append((start, k - 1))
            start = k
    out = []
    for i, j in runs:
        h = x[i]
        if i == 0 or j == n - 1 or not (x[i - 1] < h and x[j + 1] < h):
            continue
        higher_left = [k for k in range(i) if x[k] > h]
        higher_right = [k for k in range(j + 1, n) if x[k] > h]
        stop_left = max(higher_left) + 1 if higher_left else 0
        stop_right = min(higher_right) if higher_right else n
        base = max(min(x[stop_left:i + 1]), min(x[j:stop_right]))
        if h - base >= floor:
            out.append({"index": (i + j) // 2, "frequency": (freqs[i] + freqs[j]) / 2,
                        "height": h, "prominence": h - base})
    return out


def case(cid, psd, want, why, floor=None, freqs=None):
    freqs = freqs if freqs is not None else [float(k) for k in range(len(psd))]
    args = {"frequencies": freqs, "psd": psd}
    if floor is not None:
        args["min_prominence"] = floor
    expected = [{"index": i, "frequency": f, "height": h, "prominence": p}
                for i, f, h, p in want]
    assert peaks(freqs, psd, floor or 0.0) == expected, (cid, peaks(freqs, psd, floor or 0.0))
    cases.append({"id": f"spectral_peaks.{cid}", "op": "spectral_peaks", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"spectral_peaks.{cid}", "op": "spectral_peaks", "args": args,
                  "error": "invalid_argument", "source": why})


case("single", [0.0, 1.0, 3.0, 1.0, 0.0], [(2, 2.0, 3.0, 3.0)],
     "one peak of 3 with both bases 0")
NESTED = [0.0, 4.0, 1.0, 3.0, 0.5, 0.0]
case("nested", NESTED, [(1, 1.0, 4.0, 4.0), (3, 3.0, 3.0, 2.0)],
     "4 has bases 0 and 0; 3's left base stops at the 4, minimum 1, right base 0: prominence 2")
case("threshold", NESTED, [(1, 1.0, 4.0, 4.0)],
     "min_prominence 3 drops the peak of prominence 2", floor=3.0)
case("threshold_equal", NESTED, [(1, 1.0, 4.0, 4.0), (3, 3.0, 3.0, 2.0)],
     "min_prominence 2 keeps the peak of prominence exactly 2", floor=2.0)
case("plateau_odd", [0.0, 2.0, 2.0, 2.0, 0.0], [(2, 2.0, 2.0, 2.0)],
     "a run of three: index and frequency at its middle bin")
case("plateau_even", [0.0, 2.0, 2.0, 0.0], [(1, 1.5, 2.0, 2.0)],
     "a run of two: index floor(3/2) = 1, frequency halfway, 1.5")
case("edges", [5.0, 1.0, 2.0, 1.0, 4.0], [(2, 2.0, 2.0, 1.0)],
     "the edge bins are never peaks; the 2 has bases 1 and 1")
case("edge_plateau", [3.0, 3.0, 1.0, 2.0, 0.0], [(3, 3.0, 2.0, 1.0)],
     "a run touching the edge is not a peak; the 2's left base stops at the 3s, minimum 1")
case("shoulder", [0.0, 2.0, 2.0, 3.0, 0.0], [(3, 3.0, 3.0, 3.0)],
     "the run of 2s rises into the 3, so it is a shoulder, not a peak")
case("equal_neighbour", [0.0, 3.0, 1.0, 3.0, 0.0], [(1, 1.0, 3.0, 3.0), (3, 3.0, 3.0, 3.0)],
     "an equal peak does not stop a base: each 3 sees both 0s, prominence 3")
case("spaced", [0.0, 1.0, 3.0, 1.0, 0.0], [(2, 150.0, 3.0, 3.0)],
     "the single peak on 50 Hz bins from 50 Hz", freqs=[50.0, 100.0, 150.0, 200.0, 250.0])
case("monotone", [1.0, 2.0, 3.0, 4.0], [], "a rising PSD has no peak")

err("negative_floor", {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, 1.0, 0.0],
                       "min_prominence": -1.0}, "min_prominence must be >= 0")
err("negative_psd", {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, -1.0, 0.0]},
    "psd must be non-negative")
err("one_bin", {"frequencies": [0.0], "psd": [1.0]}, "need at least two bins")

doc = {
    "schema": 1,
    "suite": "spectral_peaks",
    "description": "Spectral peaks (conventions: Spectra, Spectral peaks; ADR 0135).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectral_peaks.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/spectral_peaks.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
