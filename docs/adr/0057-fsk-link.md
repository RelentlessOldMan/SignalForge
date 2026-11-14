# ADR 0057: FSK in the link

Status: accepted, 2026-11-13

## Context

`qpsk_link` runs QPSK, 16-QAM, 8-PSK and 64-QAM through one channel and receiver chain
([ADR 0050](0050-link-modulation.md)). FSK ([ADR 0054](0054-fsk.md)) has a modulator, a
noncoherent detector and a closed-form error rate, but nothing runs it end to end. FSK differs
from the others in ways the chain cannot hide: it is not pulse shaped, its detector needs no
carrier estimate, and it has no constellation to measure EVM against.

## Decision

- `modulation` also takes `"fsk2"` and `"fsk4"`: continuous-phase FSK with modulation index 1
  (orthogonal tones, the case `fsk_ber_theory` describes), `M` = 2 or 4.
- The transmitter is `fsk_modulate` of the PRBS bits, unit amplitude, after the same delay. The
  channel is the same; the AWGN's nominal signal power is 1 instead of `1/sps`.
- The receiver has no matched filter and no carrier recovery. Like the PSK chain it finds the
  symbol timing first and the frame second. The timing is the sample phase where the
  noncoherent detector's largest tone energy, summed over the whole stream, is greatest. The
  frame is the offset at that phase where the energy of the preamble's known tones is greatest.
  `fsk_demod_noncoherent` then decides the frame's bits. This is the "noncoherent detection after
  preamble timing" of the plan, and it needs nothing the detector does not already compute.
- The preamble alone was tried first and rejected: over a 32-symbol preamble the energy one
  sample early is only a few percent below the peak, so with noise the search often landed one
  sample early (10% of runs for 2-FSK at 4 samples per symbol and 7 dB, a third at 8 samples),
  and those runs had several times the errors. The whole stream averages that noise away.
- The received samples are padded with zeros back to the transmitted length plus one symbol, so
  a clock offset that shortens the stream cannot push the true offset out of the search.
- The report keeps its shape. `timing_offset` and `frame_start` are the found offset modulo
  `sps` and divided by `sps`. `frequency_offset_hz`, `phase_offset` and `evm` are none: the
  receiver estimates no carrier and has no symbols to measure. They become optional in both
  languages (`double?`, `Evm?` in C#), which the JSON already allows (`null`). `ber_theory` is
  `fsk_ber_theory`.
- Options that only mean something for the PSK/QAM chain (`timing_loop_gains`,
  `carrier_loop_gains`) are rejected with FSK instead of being ignored. `rolloff`, `span_symbols`
  and `phase_block_symbols` are checked as before (`rrc_taps` must accept them) and unused, so one
  config can switch modulation.
- `samples_per_symbol` must be at least `M`, so no tone aliases onto another.

## Consequences

- An FSK link and its error rate can be checked against `fsk_ber_theory` like the others, and
  compared across languages by statistics.
- A frequency offset is not corrected. With index 1 the tones are a symbol rate apart, so an
  offset of a few percent of the symbol rate costs little, and a large one breaks the link; the
  report shows that as errors, not as an estimate.
- The timing is fixed for the whole frame; a large clock offset with few samples per symbol drifts
  out of it and shows as errors (no timing tracking for FSK yet).
- Report users must handle the optional fields. Higher FSK orders, other indices and an FSK
  frequency estimate can be added later without changing these fields again.
