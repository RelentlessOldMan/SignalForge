# 0007: Pulse shaping, AWGN channel, EVM and BER theory

Date: 2026-11-13. Status: accepted.

## Context

The QPSK link slice (status: Next) needs root-raised-cosine (RRC) pulse shaping and its matched
filter, noise at a stated Es/N0, a frequency offset, EVM, and the theoretical BER to compare
against. Each has several common definitions (tap normalization, what "Es" is measured over, what
EVM is normalized to), so one has to be chosen and written down before the two implementations are.

## Decision

- **New modules** `dsp` (`signalforge.dsp` / `SignalForge.Dsp`: convolution, upsampling, RRC taps,
  pulse shaping) and `channel` (`signalforge.channel` / `SignalForge.Channel`: AWGN, frequency
  offset). EVM and BER theory go in `metrics`. Definitions are in `docs/conventions.md` (Pulse
  shaping, Channel, EVM and BER).
- **RRC taps have unit energy** (`Σh² = 1`). Then the shaping filter followed by the matched filter
  (the same taps) has unit gain at the symbol instants, the shaped signal has mean power `Es/sps`
  per sample, and the matched-filter output SNR per symbol equals the channel's Es/N0. No other
  scaling is needed anywhere in the link.
- **AWGN is set by Es/N0 with the signal power measured** from the samples by default (as most
  tools do), or given explicitly for a reference power that does not depend on the data. N0 is the
  noise power per complex sample, so `σ² = P·sps / (Es/N0)`.
- **EVM is normalized to the mean power of the reference symbols supplied** (unit for our QPSK).
  This is the common "RMS EVM relative to average reference power"; standards that normalize
  differently (peak power, a fixed constellation power) get their own functions in the standards
  modules.
- **erfc in C#** is written here (.NET has none): the Taylor series of erf below `x = 1.5` and a
  continued fraction above, both from their textbook definitions, with relative error below 1e-13
  against the C library's erfc (prototyped over −3 ≤ x ≤ 26). Python uses `math.erfc`. A dependency (Math.NET) for one function is not worth it.
- **Convolution is direct** (`O(N·M)`) in C#, and `numpy.convolve` (also direct) in Python. Pulse
  shaping filters are short; FFT convolution can come later behind the same function.
- **Random noise** uses NumPy's `default_rng` (PCG64) in Python and `System.Random` with a seed plus
  Box–Muller in C#. The streams differ between languages (conventions: Random numbers); vectors test
  noise only through errors, and unit tests check its statistics.

## Consequences

- With unit-energy taps and Es/N0 set this way, a simulated QPSK link's BER can be compared with
  `qpsk_ber_theory(Eb/N0)` directly, with `Es/N0 = Eb/N0 + 10·log10(2)`.
- Measured-power AWGN depends slightly on the data; tests that compare against theory pass the
  nominal power (`1/sps` for unit symbols and unit-energy taps) instead.
