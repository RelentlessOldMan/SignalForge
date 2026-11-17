# ADR 0198: Coherent output power

Status: accepted, 2026-11-16. It builds on the coherence (ADRs 0192 and 0197).

## Context

The coherence `γ²` says what fraction of the output power at each frequency is linearly related
to the input. Splitting `Pyy` into that part and the rest gives the coherent output power and
the noise (or nonlinear) spectrum. It is a standard way to read a transfer-function
measurement.

## Decision

- **The API.**
  - Python: `coherent_output_power(x, y, sample_rate, *, nperseg=None, noverlap=None,
    window="hann", beta=None, detrend="none", nfft=None)` in `spectral`.
  - C#: `Spectral.CoherentOutputPower`, with real and `Complex` overloads.
  - Both return `CoherentOutputPower(frequencies, coherent, noncoherent, num_segments)`.
- **The definition.**
  - `Pyy` is `welch_psd(y)` with the same arguments: one-sided and doubled for real input,
    two-sided and shifted for complex input (ADR 0197).
  - `γ²` is the coherence on the same bins.
  - `coherent = γ²·Pyy` and `noncoherent = Pyy − coherent`, so the two sum to `Pyy`.
- **No NaN.** Where the coherence is undefined, the split is fixed:
  - Where `Sxx·Syy = 0`, `γ²` is taken as 0.
  - Where `Syy = 0`, both parts are 0.
  - Where only `Sxx = 0`, all the output power is noncoherent: nothing in `y` there is related
    to `x`.
- **The rules.** They are those of `coherence`: finite, one-dimensional, the same length, and
  the Welch segment rules.

## Consequences

- **Vectors.** They are hand DFTs of rectangular segments:
  - a scaled copy, where the noncoherent part is 0;
  - three segments that disagree;
  - a doubled bin;
  - a silent input, and a silent output;
  - a complex pair.
- **A unit test** checks that the two parts sum to `welch_psd(y)`.
