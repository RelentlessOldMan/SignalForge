# ADR 0316: Supersaw

Status: accepted, 2026-11-18.

## Context

A supersaw stacks several sawtooths detuned a few cents apart. The beating between them gives
the wide, chorused lead and pad sound of trance and modern pop. Built from the PolyBLEP
sawtooth (ADR 0310), it stays cheap and low in aliasing.

## Decision

- **The API.**
  - Python: `supersaw(sample_rate, num_samples, frequency, detune, voices=7, amplitude=1)` in
    `waveforms`.
  - C#: `Waveforms.Supersaw`, same arguments.
  - Real output.
- **The value.**
  - `V = voices`. Voice `k = 0 … V−1` is detuned by `c_k = detune·(2·k/(V − 1) − 1)` cents, so
    the voices spread evenly over `±detune`. With `V = 1`, `c_0 = 0`.
  - `f_k = f·2^(c_k/1200)`, computed in that order.
  - Voice `k` is the PolyBLEP sawtooth at `f_k` with amplitude 1 and phase `k/V`. The fixed,
    evenly spread phases keep the voices from starting in step, without a random stream that
    would differ between the languages.
  - `y = A·(Σ_k voice_k)/V`: the voices are summed in order of `k` and then divided, so the peak
    stays near `A`.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency` and `amplitude` finite. `detune` finite and at least 0.
  - `voices` an integer of at least 1.
  - Every `|f_k| ≤ fs/2`, the PolyBLEP sawtooth's rule.

## Consequences

- **Vectors.**
  - `2^(c/1200)` is not rational. The generator computes each `f_k` in floating point by the
    formula above with the standard library, then evaluates the voices from that `f_k`, and
    the phase `k/V` as a float, in exact rationals. The result is rounded once.
  - The PolyBLEP sawtooth is continuous in `u`. A difference of one rounding in `f_k`, between
    libraries' `pow`, therefore moves a sample by about `n·ulp` times its slope.
  - The tolerance is `abs 1e-10, rel 1e-10`.
