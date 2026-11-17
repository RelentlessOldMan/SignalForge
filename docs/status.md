# Status

Updated with every chunk of work. Dates are absolute.

## Next

1. **Coherence significance threshold**: `coherence_threshold(num_segments, alpha)` in
   `spectral` (C# `Spectral.CoherenceThreshold`). Not built yet.
   - It is the level that the coherence of two independent Gaussian signals exceeds with
     probability `alpha`, `1 − alpha^(1/(K−1))`, for `K` non-overlapping segments.
   - `alpha` is in (0, 1) and `K ≥ 2`.

   Needs an ADR covering the overlap caveat: overlapped segments are not independent, so the
   threshold uses the given `K` as is. Expected values: closed-form cases, e.g. `K = 2`,
   `alpha = 0.05` gives 0.95; `K = 11` gives `1 − 0.05^0.1`.

## Built

- 2026-11-12: repo, license (MIT), README, this brain (`CLAUDE.md`, `docs/status.md`), CI.
- 2026-11-12: research and architecture docs: conventions, architecture, testing, dependencies with
  license verification, ADRs 0001–0005 (0006 below).
- 2026-11-12: Python package `signalforge` and C# library `SignalForge` (then 0.1.0), each with:
  `Signal` with metadata; units (dB, dBm, Vrms at an impedance); complex and real tones; PRBS
  (O.150 polynomials, orders 7–31); power stats (mean, RMS, peak, PAPR, DC); QPSK Gray map and hard
  demap; bit error count.
- 2026-11-12: NumPy approved as the Python runtime dependency; its bundled GCC Fortran runtime
  (GCC runtime exception) puts no obligation on our code. ADR 0004.
- 2026-11-12: PSF-2.0 approved, MPL-2.0 allowed for dev-only tools (ADR 0005); mypy strict added to
  the Python checks and CI, tests annotated.
- 2026-11-12: shared vectors, 46 cases across units, waveforms, PRBS, measurements and modulation.
  Python 79 passed, 2 skipped (PRBS 23 and 31 full-period checks, too slow); .NET 77 passed.
- 2026-11-13: spectral module in both languages (ADR 0006): FFT (Python `numpy.fft`; C# its own
  radix-2 plus Bluestein, no dependency), frequency axes, seven windows with coherent gain and ENBW,
  Welch PSD (one- and two-sided), occupied bandwidth (β/2), channel power. 59 new vectors (105 in
  all). Python 153 passed, 2 skipped (CI: Python 3.10 and 3.13); .NET 148 passed.
- 2026-11-13: date-based versioning (`YYYY.M.D.N`, docs/versioning.md): `VERSION` at the root is the
  one source; .NET reads it at build time, `build.ps1` bumps it and stamps Python's `__version__`;
  tests in both languages check they agree. Was 0.1.0; first build 2026.11.13.0. Python 155 passed,
  2 skipped; .NET 149 passed.
- 2026-11-13: review and fixes across both languages:
  - **Bugs fixed:** occupied bandwidth could return `inf` at fraction 1 when trailing bins were zero
    (the total and the running sum differed in the last bit); a one-sided PSD undercounted DC and
    Nyquist power. New `span` argument for OBW and channel power, and `SpectralDensity.span`
    `(0, fs/2)` for one-sided PSDs (conventions: Bins as rectangles).
  - **Stricter arguments:** Kaiser β limited to 0…700 (I₀ overflows above 713); Welch takes `beta`;
    sample rates and impedances must be finite; `power_stats` and PSD frequencies reject NaN and
    infinity; QPSK bits must be exactly 0 or 1; Python counts must be integers (`3.0` is
    rejected). New conventions section: Arguments.
  - **Conformance runners:** the C# runner passed some broken cases (an argument it didn't read,
    a decoding error counted as the expected `invalid_argument`, truncated `re`/`im` pairs,
    approximate window names). Both runners now reject unknown arguments and compare types
    strictly. `vectors/selftest/must_fail.json` holds 11 wrong cases both runners must fail; it
    found one more crash in the C# runner.
  - 26 new vectors (131 in all): span cases, the fraction-1 regression, Kaiser and Welch β,
    non-finite inputs, PRBS 11/15/20/23/31 prefixes and a PRBS7 run past its period.
  - Docs and tooling: build.ps1 refuses a missing or malformed `VERSION`; CI actions updated to the
    current node24 majors; NumPy floor raised to 2.2 (the oldest version CI tests); README in the
    REPO-SETUP form; NuGet metadata. Two license questions are open for the user (dependencies.md):
    libquadmath (LGPL) in NumPy's Linux wheels, and NumPy's vendored permissive parts.
  - Python 207 passed, 2 skipped; .NET 189 passed.
- 2026-11-13: QPSK link building blocks in both languages (ADR 0007): modules `dsp` (convolution,
  upsampling, unit-energy RRC taps, pulse shaping) and `channel` (seeded AWGN at Es/N0, frequency
  offset); in `metrics`, EVM (RMS, %, dB, peak) and QPSK BER theory, with C#'s own erfc. 49 new
  vectors (180 in all); RRC expected values come from the inverse Fourier transform of the
  root-raised-cosine spectrum (Gauss–Legendre), not the closed form. Unit tests check AWGN
  statistics, the matched filter's Nyquist property, and a shaped QPSK link's BER against theory
  at 4 dB Eb/N0 in both languages. Python 278 passed, 2 skipped; .NET 259 passed.
- 2026-11-13: review of the link blocks. Python raised `OverflowError` (not `ValueError`) for an
  extreme Es/N0 or Eb/N0, where C# quietly returned infinity: AWGN now rejects an Es/N0 so low the
  noise variance overflows (both languages), and BER theory returns 0 above about 3080 dB. CI's
  Python 3.10 mypy (NumPy 2.2 stubs) failed on two annotations; fixed and checked locally on 3.10.
  2 new vectors (182). Python 283 passed, 2 skipped (also on 3.10); .NET 261 passed.
- 2026-11-13: block synchronization ([ADR 0008](adr/0008-block-synchronization.md)), new module
  `sync` in both languages: Oerder–Meyr symbol timing (`timing_offset`), fourth-power QPSK carrier
  frequency (`qpsk_frequency_offset`) and phase (`qpsk_phase_offset`), each a feed-forward block
  estimate; correction reuses `frequency_offset`. 24 new vectors (206), built from clean signals
  where each estimator is exact. Unit tests run a shaped QPSK link with delay, carrier offset, phase
  and noise, recover it, and check BER against theory at 6 dB. Python 312 passed, 2 skipped; .NET
  290 passed.
- 2026-11-13: review of `sync`. The estimators are scale-invariant, but `z⁴` underflowed to 0 for
  symbols near 1e-90 (estimate 0) and overflowed near 1e80 (NaN). Both languages now scale each block
  by a power of two first, which is exact, so earlier results are bit-identical. 6 new vectors
  (212); five of them fail on the old code. Python 318 passed, 2 skipped; .NET 296 passed.
- 2026-11-13: end-to-end QPSK link ([ADR 0009](adr/0009-qpsk-link-report.md)), new module `link`
  in both languages: `qpsk_link(QpskLinkConfig)` runs PRBS bits through RRC shaping, delay, carrier
  offset and AWGN, recovers timing, frame start (preamble search), frequency and phase, and returns
  `QpskLinkReport` with EVM, bit errors and theory BER, writing the same JSON in both languages.
  The coarse fourth-power frequency estimate alone left BER 200 times theory at 6 dB, so the
  receiver adds `sync.qpsk_block_phases` (new) and a line fit through the block phases for fine
  frequency and phase. 24 new vectors (236): exact block phases, and noiseless links checked against
  the channel's own delay, offset and phase. Unit tests check BER against theory at 6 dB with three
  offsets, and the JSON field names (the same list in both languages). Python 354 passed, 2
  skipped; .NET 327 passed.
- 2026-11-13: review of `link`. In Python a NumPy integer in the config made `to_json` raise
  (`dataclasses.asdict` keeps `np.int64`), and NumPy floats or an integer Eb/N0 were rejected. The
  link now accepts any real number (not bool) and stores the config in the report as plain `int`
  and `float`. Python 355 passed, 2 skipped; .NET 327 passed.
- 2026-11-13: cross-language checks. A C# console tool (`dotnet/tools/SignalForge.Conformance`,
  built from the tests' own runner) writes the same conformance report as Python, and runs a
  `qpsk_link` config. `python -m signalforge.compare` diffs the two reports (every field of every
  result, at the case's tolerance) and compares two link reports (noiseless: every field; noisy:
  bit errors and mean squared EVM by two-sample tests). `vectors/links/` holds one noisy and one
  noiseless config; `build.ps1` and a new CI job run all of it. Vectors may now give `null`. The
  first diff found a real gap: Python's runner ignored properties, so `SpectralDensity.span` was
  never compared. Python 367 passed, 2 skipped; .NET 330 passed; vectors 237/237; reports agree.
- 2026-11-13: review of the compare tool. Both diffs compared only the fields on one side, so a
  field the other side alone had went unseen; they now check both sides' field names first. A
  noisy link compare also checks the theoretical BER (it depends only on the config). The C# tool
  printed a stack trace on a bad config or argument and now exits 2 with a message, as the Python
  one does. Python 369 passed, 2 skipped; .NET 330 passed.
- 2026-11-13: FIR filters in both languages (ADR 0010): windowed-sinc low-pass, high-pass (odd
  length) and band-pass design scaled to unit gain at DC, fs/2 or the band center; Kaiser's
  length and beta formulas; the complex frequency response; and `FirFilter`, the first operation
  with state across chunks (any split of a signal gives the same output as one call). The 38
  vectors come from `vectors/generators/fir.py`, standard library only, which integrates the
  ideal spectrum numerically rather than using the sinc formula; CI checks the file still
  matches it. The Python runner now treats a tuple result as a real array, as C# already did.
  A design whose taps have no gain to scale (a length-2 Hann window) raises instead of returning
  NaN. `link._finite` moved to `_checks.real` for reuse. A unit test caught Python's `FirFilter`
  keeping the caller's array instead of a copy. Python 422 passed, 2 skipped; .NET 376 passed;
  vectors 275/275; reports and links agree.
- 2026-11-13: Resampling in both languages (ADR 0011): `resample(x, up, down, taps)` by a
  rational factor reduced by its gcd, with the filter delay removed so output `m` sits at input
  time `m·down/up`; `interpolate` and `decimate` are its two special cases; default taps
  `resample_taps` are a Hamming low-pass of 20·R + 1 taps. C# runs a polyphase loop that skips the
  zero products; Python convolves the zero-stuffed signal. The 20 vectors come from
  `vectors/generators/resample.py` (standard library, brute-force sum) and hand derivations.
  Review fix: integer arguments now reject bools in Python (`True` used to pass as 1), as reals
  already did.
- 2026-11-13: signal files in both languages (ADR 0012): `encode_samples` / `decode_samples` for
  the 18 SigMF datatypes (real and complex; f64, f32, i32, i16, i8; little and big endian), with
  integers scaled to full scale 1.0, rounded half to even, and out-of-range values rejected; and
  `write_sigmf` / `read_sigmf` for a `.sigmf-meta` + `.sigmf-data` pair carrying every `Signal`
  field (the extras in a `signalforge` extension namespace). Written from the format description;
  nothing copied from the spec or sigmf-python. 81 vectors from `vectors/generators/files.py`
  (standard library `struct`), with 16 recordings in `vectors/files/`, including foreign-written and
  malformed ones. New cross-language check: each language writes a recording per datatype, both
  read all of them, and `compare files` checks the reads match exactly and the two writers agree
  within one quantization step (`build.ps1`, CI). Review fixes found on the way: the runners turned
  a complex value with an infinite part into NaN (Python) or failed to match it (C#); C# read JSON
  integers as doubles (a ternary promoted `long` to `double`).
  Python 585 passed, 2 skipped (3.10 too); .NET 515 passed; conformance 376/376 in both.
- 2026-11-13: spectrogram in both languages (ADR 0013): Welch's segments kept one per row, same
  windowing, scaling and sidedness, rows timed at segment centers; Welch now shares the segment
  code. 13 vectors from `vectors/generators/spectrogram.py` (standard library, DFT summed term by
  term) and a hand-derived tone; both runners now read and compare 2-D results.
  Python 604 passed, 2 skipped (3.10 too); .NET 533 passed; conformance 389/389 in both.
- 2026-11-13: IIR filters in both languages (ADR 0014): second-order sections, Butterworth
  low-pass and high-pass by the prewarped bilinear transform with a fixed section order and unit
  gain per section, `sos_response`, and a streaming `IirFilter` shaped like `FirFilter`. 26 vectors
  from `vectors/generators/iir.py` (real biquad formulas, a different route from the library's
  pole mapping) plus hand cases; unit tests check every design against the closed-form magnitude.
  The runners share one chunked-filter op. Python 713 passed, 2 skipped (3.10 too); .NET 589
  passed; conformance 415/415 in both.
- 2026-11-13: `build.ps1` runs every vector generator's `--check`, as CI already did, so a stale
  vector file fails locally before a push.
- 2026-11-13: more waveforms in both languages: `multitone` (chosen phases, or `newman_phases`),
  linear `chirp` (reaches `stop` at N/fs) and `pulse_train` (whole samples, floored modulo, any
  delay). `tone` now rejects non-finite frequency, amplitude and phase in both. 29 vectors from
  `vectors/generators/stimuli.py` (standard library, formulas sample by sample) plus hand cases.
  Unit tests: Newman phases cut a 32-tone crest factor below 0.4 of √32, chirp instantaneous
  frequency is linear and two chirps join without a jump. Python 779 passed, 2 skipped (3.10
  too); .NET 627 passed; conformance 444/444 in both.
- 2026-11-13: review of the signal files, spectrogram and IIR slices (no wrong numbers found):
  the two languages now apply one set of JSON limits to SigMF meta (int64 integers, finite floats,
  valid Unicode, 64 levels, `null` captures or metadata rejected), and Python checks everything
  before writing either file, as C# did. Python `write_sigmf` accepts NumPy scalars in the signal,
  `decode_samples` counts a memoryview's bytes, and a huge JSON integer or a bool sample rate is a
  `ValueError`. 24 new vectors, 23 of them errors (files, IIR, spectrogram); the C# runner reads an empty `sos`.
  Python 809 passed, 2 skipped (3.10 too); .NET 655 passed; conformance 468/468 in both.
- 2026-11-13: tone metrics in both languages (ADR 0015): `tone_metrics` / `Measurements.ToneMetrics`
  gives SNR, SINAD, THD and ENOB of the strongest (or a named) tone from one windowed spectrum of
  the whole input. Bins are grouped DC, fundamental, aliased harmonics, noise, each bin once, with
  a half-width set by the window; the fundamental's frequency is its group's power centroid.
  18 vectors (`generators/tone_metrics.py`) built from on-bin tones whose group powers are known
  in closed form, including aliased harmonics of a complex tone and the Hann 1/6 : 2/3 : 1/6 split.
  Python 839 passed, 2 skipped (3.10 too); .NET 681 passed; conformance 486/486 in both.
- 2026-11-13: SFDR in both languages: `sfdr` / `Measurements.Sfdr` gives the carrier and up to
  `num_spurs` spurs (group power, power centroid, dBc), strongest peak bin first, DC never a spur,
  from the same groups as the tone metrics; both languages now share one grouping helper. 7 more
  closed-form vectors in `tone_metrics.json`, among them a named carrier below its spur (negative
  SFDR) and a spectrum with no bin left for a spur.
  Python 851 passed, 2 skipped (3.10 too); .NET 689 passed; conformance 493/493 in both.
- 2026-11-13: band-pass and band-stop Butterworth in both languages (`butterworth_bandpass`,
  `butterworth_bandstop`; ADR 0016): the low-pass prototype transformed to the band, one section
  per band pole pair, scaled by the analog factors so the cascade's gain is exactly the closed form.
  16 more `iir.json` cases (two by hand, seven designs the generator checks against the closed-form
  magnitude before writing, responses, a filter run, six errors).
  Python 926 passed, 2 skipped (3.10 too); .NET 716 passed; conformance 511/511 in both.
- 2026-11-13: zero-phase filtering in both languages (`zero_phase_filter` /
  `Dsp.ZeroPhaseFilter`, ADR 0017): forward then backward over an odd extension, each pass from
  the sections' steady state. 12 more `iir.json` cases (two by hand, a constant that must come back
  exactly, five from a direct form I implementation, five errors).
  Python 949 passed, 2 skipped (3.10 too); .NET 732 passed; conformance 523/523 in both.
- 2026-11-13: review fixes for tone metrics, SFDR, band Butterworth and zero-phase filtering.
  Tone metrics: bins at or below 1e-20 of the total power are zeroed (rounding error had picked
  fundamentals and spurs that differed between languages); a non-finite spectrum is an error; the
  C# half-width is clamped (it overflowed near `int.MaxValue`); a complex fundamental of +fs/2
  means the -fs/2 bin. Zero-phase filtering rejects non-finite samples. The band generator now
  checks stability and the denominator product against a polynomial expansion of the analog
  prototype, independent of the pole algorithm. The C# runner rejects `2.0` for an integer
  argument. 26 more vectors (tone 9, iir 17); C# band tests match Python's 40 cases.
  Python 981 passed, 2 skipped (3.10 too); .NET 793 passed; conformance 549/549 in both.
- 2026-11-13: Chebyshev type I low-pass and high-pass in both languages (`chebyshev1_lowpass`,
  `chebyshev1_highpass` / `Dsp.Chebyshev1Lowpass`, `Chebyshev1Highpass`, ADR 0018): pass-band
  ripple in dB, the cutoff the pass-band edge, sections shared with Butterworth's builder (a test
  annotation fixed for NumPy on Python 3.10 in the next build). 20 more
  `iir.json` cases (two designs by hand, eight checked against the closed form, a response, a
  filter run, eight errors).
  Python 1061 passed, 2 skipped (3.10 too); .NET 854 passed; conformance 569/569 in both.
- 2026-11-13: ACPR in both languages (`acpr` / `Spectral.Acpr`, ADR 0019): main channel and lower
  and upper channels at each center-to-center offset, by the channel power rule, in dBc; a channel
  that leaves the spectrum is an error. New `vectors/generators/acpr.py` writes `acpr.json`
  (15 cases, the powers summed from piecewise-constant bins by hand). Tests: on-bin tones through
  Welch (-20 and -40 dBc), flat noise (the bandwidth ratio), bad arguments.
  Python 1086 passed, 2 skipped (3.10 too); .NET 877 passed; conformance 584/584 in both.
- 2026-11-13: Chebyshev type II low-pass and high-pass in both languages (`chebyshev2_lowpass`,
  `chebyshev2_highpass` / `Dsp.Chebyshev2Lowpass`, `Chebyshev2Highpass`, ADR 0020): flat pass
  band, stop-band peaks at `-attenuation_db`, the cutoff the stop-band edge; the shared cascade
  builder now takes zeros on the unit circle. Fix found while designing it: a type I ripple above
  about 3080 dB raised OverflowError in Python, not ValueError, and past ~200 dB the poles sit on
  the unit circle to rounding, so ripple and attenuation are now limited to (0, 200] dB. 20 more
  `iir.json` cases (two designs by hand, eight computed from the analog quadratics and checked
  against the closed form, a response, nine errors incl. two type I ones).
  Python 1176 passed, 2 skipped (3.10 too); .NET 940 passed; conformance 604/604 in both.
- 2026-11-13: review pass over the spectral measurements and the IIR designs, fixes in both
  languages. IIR: a cutoff or band edge within ~1e-8·fs of 0 or fs/2 rounded a pole onto the unit
  circle (Butterworth gain 0, a pole at z = 1; Chebyshev II raised ZeroDivisionError in Python and
  gave NaN in C#); every design now checks its sections are finite and strictly stable and
  rejects the rest. The Chebyshev II reference gain uses the exact denominators. dB values enter
  as `expm1` (C#: a series below 1e-5), so a 1e-17 dB ripple no longer divides by zero. Order is
  capped at 1000. Python `sos_response` rejects complex and bool frequencies. Spectral: an
  overflowing bin power or total gave NaN (Python) or IndexOutOfRangeException (C#); an infinite
  bin spacing passed in Python; bins whose half-width rounds away are rejected; a channel past the
  spectrum by rounding (`0.3 − 0.1 − 0.2`) is accepted within 1e-9 of a bin; dBc is a difference
  of logs, so a 1e-400 ratio is −4000 dBc, not −∞; Python `channel_power` validates its edges
  (no TypeError/OverflowError); C# names `center` when the main channel leaves the spectrum.
  Conventions updated; 8 more `iir.json` and 5 more spectral/ACPR cases.
  Known weakness, not fixed: the band-form vectors come from a generator that follows the same
  pole-pair construction as the code; an independent root-finding check would be stronger.
  Python 1208 passed, 2 skipped (3.10 too); .NET 959 passed; conformance 617/617 in both.
- 2026-11-13: band-pass and band-stop Chebyshev types I and II ([ADR 0021](adr/0021-band-chebyshev.md)):
  `chebyshev1_bandpass`, `chebyshev1_bandstop`, `chebyshev2_bandpass`, `chebyshev2_bandstop`
  (`Chebyshev1Bandpass` ... in C#), on the shared band transform that Butterworth band designs now
  also use. Conventions give the prototype frequency maps, the closed-form |H|², the type II
  zero images and the section gains. 21 new `iir.json` cases: four by-hand order-1 designs, ten
  computed designs (orders 2-5), seven rejections. The generator builds the sections from their
  own analog quadratics and checks them against the closed-form |H|² and edge values, section
  stability, and the product of the denominators against the prototype expanded by polynomial
  substitution (independent of the pole-pair split). Python 1334 passed, 2 skipped; .NET 1046
  passed; conformance 638/638 in both.
- 2026-11-13: review of the band Chebyshevs. A sweep of 1568 designs (orders 1-1000, dB 1e-9 to
  200, bands from 1e-12·fs wide to near Nyquist): each design either raises `ValueError` or
  matches the closed-form |H|² to 1e-6, except where second-order-section coefficients can't hold
  the poles (a 1e-12·fs band; 200 dB ripple). Both languages were run on the same grid and on
  800 random designs (a temporary check, not vectors). They accept and reject the same designs
  and agree to 1e-12 on random designs, 1e-6 at the extremes. No code defects found; the
  conventions now state the bandwidth and dB conditioning limits.
- 2026-11-13: elliptic (Cauer) low-pass and high-pass ([ADR 0022](adr/0022-elliptic.md)):
  `elliptic_lowpass`, `elliptic_highpass` (`EllipticLowpass`, `EllipticHighpass`), with ripple and
  attenuation in dB. Elliptic functions by the descending Landen ladder, the degree equation by
  the nome q-product, `v0` by the ladder; conventions give every step. Designs with `k' < 1e-6`
  are rejected. 17 new `iir.json` cases: three by hand (order 1 and the order-2 design with
  ε = 1 in closed form, low-pass and high-pass), eight computed (orders 3-8), six rejections
  (including the transition limit). The generator is independent of the library: it builds the rational
  function R_N from theta functions and the AGM, finds the poles as roots of D² + ε²N² (polished
  by Newton on the product form), and checks the equiripple bounds, |H|² against the closed form
  to 1e-12, and stability. A temporary sweep of 600 random designs (orders 1-1000) agreed in both
  languages to 1e-10, accepting and rejecting the same ones. Python 1388 passed, 2 skipped; .NET
  1086 passed; conformance 655/655 in both.
- 2026-11-13: review of the elliptic low/high-pass. Against the generator's independent R_N
  (theta series), 2310 designs (orders 1-30, ripple 1e-6 to 199 dB, A − R 1e-3 to 200 dB,
  cutoffs 1e-4 to 0.4999·fs) match the closed-form |H|² to 4e-9 at mid-band cutoffs and 7e-7 at
  the extreme ones. Orders 1 and 2 are never rejected; rejections are the `k' ≥ 1e-6` limit and
  the pole check. Both languages ran a 9204-design grid (orders to 1000, cutoffs to 1e-6·fs):
  they agree to 1e-7 except at cutoffs 1e-6·fs and 0.4999·fs (ill-conditioned rows, agreeing
  to about 1e-5), and accept/reject the same designs except three with 150-200 dB ripple whose
  poles sit one rounding step (2e-16) from the unit circle. No code defects; the conventions'
  conditioning note now names the elliptic ripple limit.
- 2026-11-13: band-pass and band-stop elliptic ([ADR 0023](adr/0023-band-elliptic.md)):
  `elliptic_bandpass`, `elliptic_bandstop` (`EllipticBandpass`, `EllipticBandstop`): the elliptic
  prototype (now a shared helper) through the ADR 0021 band builder unchanged, with the type I
  even-order gain. 14 new `iir.json` cases: two by hand (order 1, ε = 1, W = 1, B = 2), seven
  computed (orders 2-6, narrow and wide bands), five rejections. The generator puts its own
  theta-series prototype through the band transform and checks the closed-form |H|², the edges,
  the band-stop center, stability and the denominator product by polynomial substitution; the
  library matches it to 2e-15. A temporary sweep of 800 random band designs agreed in both
  languages to 1e-10. Python 1437 passed, 2 skipped; .NET 1123 passed; conformance 669/669 in
  both.
- 2026-11-13: review of the band elliptics. Against the generator's theta-series R_N, 1005
  designs (orders 1-30, ripple 1e-6 to 199 dB, bands from 1e-9·fs wide and edges from 1e-6·fs
  to 0.4999·fs) match the closed-form |H|² to 3e-9 for ordinary bands; the worst errors (2e-2,
  3e-2) need two limits at once (100 dB ripple in a 1e-9·fs band, order 30 with edges at
  1e-6·fs), and order 1, which is Chebyshev I, shows the same loss, so it is the band transform's
  conditioning already in the conventions. Both languages ran a 4032-design grid (orders to
  1000, the same bands, ripple from 1e-9 dB): all agree to 1e-7 and accept and reject the same
  designs. No defects found.

- 2026-11-13: equiripple FIR design ([ADR 0024](adr/0024-equiripple-fir.md)):
  `fir_equiripple(num_taps, bands, desired, sample_rate, weights=None, grid_density=16)`
  (`FirEquiripple`), symmetric type I and II, piecewise-constant bands with weights. The grid,
  the Remez exchange's tie rules and the stop rule are in the conventions, so the result is the
  unique discrete optimum on a defined grid. Two numerical traps found and fixed on the way: an
  optimum with an extra ripple makes the exchange swap between two equally good sets forever
  (now also stopped by the gap between the largest error and δ), and rebuilding the taps by
  sampling the interpolant on a uniform grid magnifies rounding in the transition gaps (a 41-tap
  design measured 2e-8 instead of 3e-11; now a direct solve at the final set). The returned taps
  are verified on the grid. Near the precision limit (ripple about 1e-13) the languages may
  differ in whether a design raises, so that is a unit-test property, not a vector. New
  generator `vectors/generators/equiripple.py`: 50-digit Remez by cosine-basis solves and
  Clenshaw evaluation, each result certified by alternation; 33 cases (seven by hand, nine
  certified, 17 rejections). The library matches to 1e-14, except 2e-11 on a design with
  δ = 3e-9 whose taps are ill-determined in double. Python 1480 passed, 2 skipped; .NET 1166
  passed; conformance 702/702 in both.

- 2026-11-13: equiripple review. A random sweep against the generator's 50-digit solver (300
  designs to 70 taps) and Python against C# (481 designs to 400 taps) found two defects, both
  fixed in both languages and the conventions: (1) a first extremal set lying only in bands whose
  desired value is 0 gives `δ = 0` and too few extrema, and rounding at the set's last point
  could flip a sign, which raised on ordinary designs: the old set's points now always count in
  the exchange, with their exact error `±δ`; (2) the final tap check's 1e-6 margin rejected usable
  designs whose coefficients are large (wide gaps between bands), where rounding alone exceeds
  it: now 0.1%, which still catches the failures it is for. False rejections in the sweep fell
  from 205 to 158 of 481 (most of the rest are beyond double precision). Python no longer warns
  on an IEEE division by zero at the precision limit. New vector `zero_delta_start` (34 cases),
  a regression test per language. Python 1482 passed, 2 skipped; .NET 1168 passed; conformance 703/703 in both.
- 2026-11-13: Bessel IIR design, `bessel_lowpass` and `bessel_highpass` (`BesselLowpass`,
  `BesselHighpass`), ADR 0025: maximally flat delay, normalized to −3 dB at the cutoff, order 1 to
  10 (the reverse Bessel polynomial's roots lose digits fast beyond), poles by Aberth's iteration
  on the recurrence, through the existing cascade. Vectors: order 1 and 2 by hand, the rest from
  50-digit roots of the exact integer coefficients and a 50-digit `ω₀`, each checked against the
  closed-form `|H|²`; tests check −3 dB, monotonic magnitude, the flat delay against
  Butterworth's and the order-2 delay at DC (`ω₀/(2K)`).
- 2026-11-13: equiripple start by reference scaling (conventions, ADR 0024): above 16 cosine
  terms the design with half as many is solved first and its final set stretched along the bands
  to start the exchange. On the 481-design random sweep Python's raises fell from 158 to 136
  (C# 147); the rest are at the precision limit (relative ripple near 1e-13 or below, or taps so
  large that their cancellation leaves no digits). Where both languages design, ordinary ripples
  agree to 4 digits or better; taps differ only in designs whose taps reach 1e3 to 1e10, where
  they are determined only to rounding times their size.
- 2026-11-13: Hilbert transformers and differentiators (conventions: Equiripple design,
  ADR 0026): `fir_equiripple(..., kind="hilbert" | "differentiator")`, C# `EquirippleKind`.
  Antisymmetric taps (types III and IV) through the same exchange with `Q = sin(2πν)` or
  `sin(πν)`; `desired` 1 is the ideal (Hilbert `H = −j`, differentiator the derivative per
  sample), a differentiator's error relative to the slope where `desired ≠ 0`; a target that
  cannot be met where `Q = 0` raises. Vectors: three hand designs with `L = 1`, nine certified by
  the 50-digit generator (extended to types III and IV), five errors. Tests: a Hilbert
  transformer turns cos into sin, a differentiator gives the derivative, taps exactly
  antisymmetric.
- 2026-11-13: streaming resampling (conventions: Resampling, ADR 0027): `Resampler(up, down,
  taps=None)` with `process`, `reset` and `taps`, like `FirFilter`. Its causal stream
  `z[m] = L·Σ h[k]·u[mM − k]` is `resample` with the taps delayed by `N − 1`; after `n` inputs
  exactly `⌈nL/M⌉` outputs have come out, however the input was split. Taps of any length (even
  too); the default is `resample_taps`, or `[1]` at 1/1. Polyphase, `⌈N/L⌉` taps per phase.
  Vectors: one by hand, seven from the generator's term-by-term causal sum (cross-checked there
  against its delayed-taps `resample`), three errors. Tests: the identity with `resample` over
  random splits, complex input with even taps, reset, the real/complex kind fixed until reset.
- 2026-11-13: group delay (conventions: FIR filters and IIR filters, Group delay; ADR 0028):
  `fir_group_delay(taps, frequencies, sample_rate)` and `sos_group_delay(sos, ...)`, in samples,
  closed form per polynomial (`Re(R/P)`, sections add as numerator minus denominator), NaN where a
  polynomial is within rounding of 0 (a zero on the unit circle). Vectors: nine by hand (pure
  delay, linear phase, the NaN points, first-order and all-pass sections, `a0` scaling), four from
  a stdlib generator that expands chosen roots into taps and sums each root's own closed-form
  delay, six errors. Tests: both agree with a numerical phase derivative, sections add, linear
  phase taps give `(N − 1)/2`, and the Bessel low-pass delay is flat to 1% up to half the cutoff
  where the Butterworth's varies by 30% and more.
- 2026-11-13: least-squares FIR design (conventions: FIR filters, Least-squares design; ADR 0029):
  `fir_least_squares(num_taps, bands, desired, sample_rate, weights=None)`, symmetric taps (odd
  or even) minimizing the exact weighted integral squared error, `desired` given at both edges of
  each band and linear between. The normal equations are built from closed-form integrals and
  solved directly. Vectors: five by hand (orthogonal cosines over `[0, fs/2]`), seven from a
  stdlib generator that checks the integrals by Simpson quadrature and solves exactly in
  rational arithmetic (up to 101 taps), nine errors. Tests: symmetric perturbations only raise the
  error, lower error energy than the equiripple design, type II zero at `fs/2`, a sloped band
  followed.
- 2026-11-13: Welch options (conventions: Spectra, PSD; ADR 0030): `detrend` ("none",
  "constant", "linear") per segment before the window, in `welch_psd` and `spectrogram`, and
  `average="median"` in `welch_psd`, the per-bin median divided by `b(K)`, the exact expected
  median of `K` unit-mean exponentials (odd and even `K`). C#: `Detrend`, `WelchAverage`. Vectors
  (`welch.json`): five by hand, twelve from a stdlib generator that detrends by the uncentred
  normal equations and checks `b(K)` by integrating the order-statistic densities, three errors.
  Tests: detrending ignores an added constant or line (real and complex), the median is unbiased
  for white noise (odd and even `K`), resists a burst, and reads a steady tone `1/b(K)` high.
- 2026-11-13: zero padding (conventions: Spectra, PSD; ADR 0031): `nfft >= nperseg` on
  `welch_psd` and `spectrogram`, zeros after the windowed segment, the scale `1/(fs·Σw²)`
  unchanged so power sums keep their meaning; `bin_width = fs/nfft`, `enbw_hz` still
  `ENBW·fs/nperseg`; both results gain `nfft` (C#: `Nfft`, the last record member). Vectors in
  `welch.json`: one by hand, six generated, two errors. Tests: every `nfft/nperseg`-th padded bin
  is the unpadded bin (one- and two-sided), total power kept for odd and even `nfft`.
- 2026-11-13: Bessel band-pass and band-stop (conventions: IIR filters; ADR 0032): the Bessel
  prototype's poles through the shared band transform with the type I Chebyshev gains, −3 dB at
  `low` and `high`, `1 ≤ order ≤ 10`. Vectors in `iir.json`: two order-1 cases by hand, eight from
  the 50-digit roots (checked against the closed-form `|H|²` and the substituted denominator),
  four errors; orders 9 and 10 at 1e-11, the roots' double-precision accuracy. Tests: every order
  equals the low-pass at `fs/4` read at `atan(|x|)`, order 1 is the band Butterworth.
- 2026-11-13: all-pass sections (conventions: IIR filters, All-pass sections; ADR 0033):
  `allpass_first_order(cutoff, sample_rate)` (phase `−π/2` at the cutoff) and
  `allpass_second_order(center, bandwidth, sample_rate)` (`−π` at the center, the `−π/2` and
  `−3π/2` points exactly `bandwidth` apart), one section each. Vectors in `iir.json`: four by
  hand, five checked at `H = −j, −1, j` with the edges from their closed form, five errors.
  Tests: unit magnitude, monotone phase, the group delay integrating to the total phase, power
  kept through `IirFilter`. The planned "mixing" slice was dropped: `frequency_offset` already
  is it.
- 2026-11-13: IQ imbalance and DC offset (conventions: Channel; ADR 0034):
  `iq_imbalance(samples, gain_db, phase)` with the error on the Q branch
  (`y = I + j·g·(Q·cos φ + I·sin φ)`), `iq_image_rejection_db(gain_db, phase)` and
  `dc_offset(samples, offset)`. 17 vectors in `channel.json`: by hand, and from the widely
  linear form `μx + νx̄` (independent of the branch form). Tests: a tone's DFT image matches the
  image rejection, the Q branch is `g·sin(θ + φ)`, no other bin is touched.
- 2026-11-13: 8-PSK and 16-QAM (conventions: Bits and symbols; ADR 0035): `psk8_map`,
  `psk8_demap_hard` (point `p` at `e^{jπp/4}`, label `p ⊕ (p >> 1)`), `qam16_map`,
  `qam16_demap_hard` (two Gray 4-PAM axes, first bit 0 positive, over `√10`, thresholds 0 and
  `2/√10`). 12 vectors by hand in `modulation.json`. Tests: round trips, unit energy, every
  nearest-neighbor pair differs in one bit, noise under the decision margin changes nothing. Review: a NaN symbol
  is `invalid_argument` in both demappers (Python cast it to an arbitrary integer sector).
- 2026-11-13: phase noise (conventions: Channel; ADR 0036): `phase_noise(samples, linewidth_hz,
  sample_rate, *, seed)`, a Wiener walk from `φ[0] = 0` with Gaussian steps of variance
  `2π·linewidth/fs`. Five vectors (zero linewidth, one sample, three errors); the random part is
  checked in each language against theory: the step variance, the variance over a lag, and
  `E[e^{jφ[n]}] = e^{−nσ²/2}` over 4000 runs.
- 2026-11-13: error-rate theory (conventions: EVM and BER; ADR 0037): `qam16_ber_theory`,
  `qam16_ser_theory` (closed forms), `psk8_ser_theory` and `psk8_ber_theory` (Pawula's phase-tail
  integral by Simpson, 4096 panels), all exact for our Gray labelings; the 8-PSK BER is
  `⅔·(T(π/8) + T(3π/8))`, not the `Ps/3` approximation the plan named. 36 vectors from
  `vectors/generators/error_rates.py`, which checks the 16-QAM forms against integrating the
  Gaussian over the decision intervals and gets 8-PSK from the phase density instead. Tests:
  limits, monotone, the high-SNR approximations, and Monte-Carlo runs through map, AWGN and
  demap at 8 dB (within 6 %). Python 1895 passed, 2 skipped; .NET 1519 passed.
- 2026-11-13: static multipath (conventions: Channel; ADR 0038): `multipath(samples, delays,
  gains)`, a tapped delay line with integer delays and complex gains, output as long as the input
  (tail dropped), gains not normalized. 12 vectors by hand in `channel.json`; tests against a
  dense convolution. Python 1919 passed, 2 skipped; .NET 1533 passed.
- 2026-11-13: soft demapping (conventions: Bits and symbols; ADR 0039): `qpsk_demap_llr`,
  `psk8_demap_llr`, `qam16_demap_llr` `(symbols, noise_variance)`, max-log LLRs by a search over
  the points, positive for bit 0, `noise_variance = N0`. 22 vectors (4 by hand, the rest empty
  input and errors); tests: the sign is the hard decision, QPSK equals `2√2·Re(y)/N0` exactly,
  within `ln(M/2)` of the exact log-sum LLR, scaling with `N0`. Python 1952 passed, 2 skipped;
  .NET 1563 passed.
- 2026-11-13: fractional delay (conventions: Channel; ADR 0040): `fractional_delay(samples, delay,
  *, half_width=16)`, a Kaiser-windowed sinc (β = 8) evaluated per output sample, exact shifts for
  whole-sample delays, zero outside the input. Fractional multipath is a sum of these, so
  `multipath` keeps integer delays. 15 vectors from `vectors/generators/fractional_delay.py` (the
  sum over every input sample, its own I0 series); tests: tones up to 0.25·fs within 5e-5
  (measured floor about 2e-5), exact integer shifts. Python 1976 passed, 2 skipped; .NET 1583
  passed.
- 2026-11-13: LLR statistics through the receive chain (tests only): QPSK through RRC shaping,
  AWGN, the matched filter and sampling at Es/N0 = 7 dB gives signed LLRs with mean `2·Es/N0`
  and variance twice that, within 1.5 % and 2 % (measured within 0.3 %), in both link suites.
  Python 1977 passed, 2 skipped; .NET 1584 passed.
- 2026-11-13: block fading (conventions: Channel; ADR 0041): `rician_fading(samples, k_factor,
  block_length, *, seed)`, one gain `√(K/(K+1)) + √(1/(K+1))·CN(0, 1)` per block, Rayleigh at
  K = 0, no fading at K = ∞. 6 deterministic vectors in channel.json (K = ∞, empty, bad
  arguments); tests: mean power, mean, per-axis variance for K = 0, 1, 3, 10, the Rayleigh power
  CDF, one gain per block with a short last block, seeding. Python 1998 passed, 2 skipped;
  .NET 1598 passed.
- 2026-11-13: QPSK in Rayleigh fading (conventions: EVM and BER; ADR 0042):
  `qpsk_ber_rayleigh_theory(eb_n0_db)`, `½(1 − √(γ/(1+γ)))` in a form without cancellation. 9
  vectors added to `error_rates.py`, checked there against the AWGN curve averaged over the
  exponential |g|² density; tests: limits, `1/(4γ)` asymptote, above the AWGN curve, and
  Monte-Carlo through `rician_fading` (K = 0) with coherent detection at 0, 5 and 10 dB within
  6 % (measured within 2 %). Python 2011 passed, 2 skipped; .NET 1611 passed.
- 2026-11-13: fractional timing end to end (tests): a shaped QPSK burst delayed by 0.3 … 3.9
  samples through `fractional_delay`; `timing_offset` finds it within 0.05 samples (measured
  within 0.014), undoing the fraction gives the AWGN BER within 10 %, and sampling half a sample
  or more off is over 1.3 times worse. `fractional_delay` now evaluates its kernel once per
  distinct fraction in both languages (same arithmetic, about 9 times faster on long inputs).
  Python 2015 passed, 2 skipped; .NET 1615 passed.
- 2026-11-13: Gardner timing recovery (conventions: Synchronization, Tracking loops; ADR 0043):
  `gardner_timing(samples, samples_per_symbol, kp, ki, *, start, half_width)` returns a
  `TimingRecovery` (symbols, positions, detector output); a PI loop on the step between symbols,
  held within half a symbol of nominal, reading between samples by the `fractional_delay`
  kernel (shared code in both languages). `pi_loop_gains(loop_bandwidth, damping,
  detector_gain)` gives the gains from the standard second-order formulas. 22 vectors from
  `vectors/generators/timing_loop.py` (stdlib, its own kernel and I0). Tests: the open loop
  matches `fractional_delay`; the S-curve is odd and positive when late; locks to a 2.3-sample
  offset at Eb/N0 2 dB (mean error under 0.06 samples, rms under 0.25, BER within 20 % of
  theory); on an analytic raised-cosine burst whose clock is slow by 1e-3, the
  proportional-only lag matches `−sps·δ/(kp·Kd)` within 25 % and the PI loop removes it.
  Python 2050 passed, 2 skipped; .NET 1645 passed.
- 2026-11-13: QPSK carrier tracking (conventions: Synchronization, Tracking loops; ADR 0044):
  `qpsk_carrier_tracking(symbols, kp, ki, *, phase)` returns a `CarrierRecovery` (corrected
  symbols, unwrapped phases, detector output); decision-directed, `Im{conj(d)·r}` with signed
  decisions, PI loop from `pi_loop_gains`. 12 vectors from `vectors/generators/carrier_loop.py`
  (stdlib). Tests: the proportional loop's lag on a rotating constellation is exactly
  `asin(ω/(√2·kp))` (to 1e-9), the PI loop removes it and its phase steps by `ω`; a full link
  (2.3-sample delay, carrier offset 1e-4 cycles per sample, Eb/N0 4 dB) through
  `gardner_timing` then the carrier loop recovers the offset within 5 % and the BER within
  30 % of theory. Python 2072 passed, 2 skipped; .NET 1662 passed.
- 2026-11-13: sample clock offset (conventions: Channel, Sample clock offset; ADR 0045):
  `clock_offset(samples, ppm, *, half_width)` reads the input every `1 + ppm/1e6` samples
  through the `fractional_delay` kernel (Python shares one vectorized reader with
  `fractional_delay`). 13 vectors from `vectors/generators/clock_offset.py` (stdlib). Tests: a
  tone comes out at the new rate within 5e-5 from −1e5 to 1e5 ppm with the expected length;
  `gardner_timing` follows a 200 ppm offset (4.8 samples of drift over 6000 symbols) with no
  growing lag and no bit errors. Python 2096 passed, 2 skipped; .NET 1683 passed.
- 2026-11-13: tracking loops in the QPSK link (conventions: QPSK link; ADR 0046): config fields
  `clock_offset_ppm`, `timing_loop_gains` and `carrier_loop_gains` (pairs `[kp, ki]`, off by
  default, so existing reports are unchanged). The timing loop replaces the fixed-phase
  decimation, starting at the block estimate; the carrier loop runs after the block correction.
  Tests: at 400 ppm over 3000 symbols the fixed sampling loses lock (BER > 0.1) and the loops
  bring it back within 5 sd of theory; without an offset the loops change EVM by under 0.02.
  Link configs `qpsk_tracking` (noisy) and `qpsk_tracking_noiseless` run in both languages and
  compare. Python 2104 passed, 2 skipped; .NET 1687 passed.
- 2026-11-13: phase noise in the QPSK link (ADR 0047): `phase_noise_linewidth_hz`, applied after
  the carrier offset; one generator seeded with `seed` drives the phase noise and then the AWGN,
  so links without phase noise are unchanged. The carrier loop now starts at the preamble's
  data-aided phase (the block line's phase at the frame start can be off by more than π/4 under
  wander, which locked the loop to the wrong quadrant). Tests: at 0.15 Hz (0.03 rad per symbol),
  over 5 seeds, the block receiver makes over 300 errors and the loop under 40 (theory about 6).
  Link config `qpsk_phase_noise`. Python 2107 passed, 2 skipped; .NET 1689 passed.
- 2026-11-13: 8-PSK and 16-QAM carrier loops (conventions: Synchronization, Tracking loops;
  ADR 0048): `psk8_carrier_tracking` and `qam16_carrier_tracking`, the QPSK loop with the
  hard demapper's decision (one shared loop in each language). 13 more vectors in
  `carrier_loop.py`, including by-hand detector values. Tests: the 8-PSK proportional lag is
  exactly `asin(ω/kp)`; the PI loop removes the lag for both; both track a drifting carrier
  through noise at Es/N0 22 dB with no bit errors; 8-PSK locks to a multiple of π/4. Python 2136
  passed, 2 skipped; .NET 1710 passed.
- 2026-11-13: power-spectrum frequency offset (conventions: Synchronization; ADR 0049):
  `power_frequency_offset(symbols, symbol_rate, power)`, the periodogram peak of `zᵖ`
  (zero-padded FFT, at least 4 bins per symbol) refined by 60 bisection steps on the sign of the
  periodogram's slope. The lag-1 `qpsk_frequency_offset` is swamped by 16-QAM's self-noise (9 Hz
  rms on 400 noiseless symbols at 1000 Bd); this is under 0.1 Hz there, under 0.05 Hz on 2000
  symbols at Eb/N0 8 dB, and works on 8-PSK at power 8. 12 new vectors in `sync.json` (tones and
  PSK symbols, where `zᵖ` is one tone and the estimate is exact). Python 2161 passed, 2 skipped;
  .NET 1727 passed.
- 2026-11-13: 16-QAM in the link (conventions: QPSK link; ADR 0050): a `modulation` config field,
  `"qpsk"` (default, reports unchanged) or `"qam16"`, choosing the mapper, the coarse frequency
  estimate (`power_frequency_offset(·, Rs, 4)` for 16-QAM), the carrier loop's decision, the
  demapper and the BER theory; Es/N0 = Eb/N0 + 10·log10 k. The block phases and the preamble's
  π/2 resolution are shared. Link configs `qam16_8db` (20000 symbols: 744 bit errors in Python,
  765 in C#, theory 740) and `qam16_noiseless` (0 errors in both). Python 2169 passed, 2 skipped;
  .NET 1734 passed.
- 2026-11-13: 8-PSK in the link (conventions: Synchronization, QPSK link; ADR 0051):
  `psk8_phase_offset` and `psk8_block_phases` (eighth power, π/4 ambiguity, 10 vectors), and
  `"psk8"` as a `modulation` value: coarse frequency from `power_frequency_offset(·, Rs, 8)`, the
  preamble rounds to π/4. Link configs `psk8_10db` (20000 symbols: 56 bit errors in Python, 62 in
  C#, theory 61) and `psk8_noiseless` (0 errors in both). Python 2200 passed, 2 skipped; .NET
  1759 passed.
- 2026-11-13: 64-QAM (conventions: Bits and symbols, EVM and BER; ADR 0052): `qam64_map`,
  `qam64_demap_hard`, `qam64_demap_llr`, `qam64_ber_theory`, `qam64_ser_theory`. Gray 8-PAM axes
  (`(1 − 2a)·(4 + (1 − 2b)·(3 − 2c))/√42`), threshold ties to bit 0; the BER is Cho and Yoon's
  square-QAM sum written out for 8-PAM, which the error-rate generator checks against an integral
  over the decision intervals (to 1e-10). 10 modulation and 16 error-rate vectors; Monte Carlo at
  12 dB within 5 % in both languages. Python 2237 passed, 2 skipped; .NET 1793 passed.
- 2026-11-13: 64-QAM carrier loop and link (ADR 0053): `qam64_carrier_tracking` (decisions as in
  `qam64_demap_hard`, ties included; 7 carrier-loop vectors) and `"qam64"` as a link
  `modulation` (fourth-power coarse frequency and block phases, π/2 resolution). 32-symbol phase
  blocks are too noisy for 64-QAM at 14 dB (the unwrapping slips; BER 0.43), 64 and longer work,
  so 64-QAM configs set `phase_block_symbols`. Link configs `qam64_14db` (273 bit errors in
  Python, 275 in C#, theory 258) and `qam64_noiseless` (0 in both). Python 2247 passed,
  2 skipped; .NET 1803 passed.
- 2026-11-13: Binary and M-ary FSK (conventions: Bits and symbols, FSK; EVM and BER; ADR 0054):
  `fsk_modulate` (continuous phase, orders 2–16, natural binary labels, the phase from an exact
  integer sum of past levels), `fsk_demod_noncoherent` (square-law correlator bank, ties to the
  smallest label), `fsk_ser_theory` and `fsk_ber_theory` (noncoherent orthogonal closed form).
  New generator `vectors/generators/fsk.py` (76 cases) checks the closed form against the
  detector's Rician/Rayleigh error integral to 1e-9. Monte Carlo within 15 % in both languages
  (about 500 symbol errors each; over 10 seeds C# averages 0.97–1.03 of theory). Python 2345
  passed, 2 skipped; .NET 1895 passed.
- 2026-11-13: WAV files in both languages (ADR 0055): `write_wav(path, channels, sample_format)`
  and `read_wav(path)`, one real `Signal` per channel; PCM `u8`/`i16`/`i24`/`i32` with the SigMF
  integer scaling (nothing clipped) and IEEE `f32`/`f64`. Writing uses one fixed layout (plain PCM
  or float `fmt `, `fact` for float, pad byte); reading also takes `WAVE_FORMAT_EXTENSIBLE`,
  unknown chunks and a wrong RIFF size, and rejects compressed formats, other bit depths, a wrong
  block align and partial frames. New generator `vectors/generators/wav.py` writes
  `cases/wav.json` (67 cases: exact file bytes for writes, 34 fixture files for reads); its PCM
  headers are checked against Python's `wave` module, an independent writer. `files.py --check`
  now only looks at SigMF files in `vectors/files/`. Python 2448 passed, 2 skipped; .NET 1979
  passed; conformance 1241/1241 in both. Version 2026.11.13.77.
- 2026-11-13: NumPy `.npy` files in both languages (ADR 0056): `write_npy(path, x)` and
  `read_npy(path)` (C# `WriteNpy`, `ReadNpy<T>`) for 1-D `'<f8'` and `'<c16'` arrays. Writing uses
  the layout `numpy.save` writes (version 1.0, data at byte 128; the Python tests compare bytes
  with `numpy.save` and read back with `numpy.load`). Reading takes versions 1.0 to 3.0 and
  parses the header with a small grammar, the same in both languages, never evaluating it; other
  dtypes, shapes, keys and data sizes are rejected. New generator `vectors/generators/npy.py`
  writes `cases/npy.json` (45 cases: exact bytes for writes, 37 fixture files for reads, NumPy
  and other writers' headers and broken ones). Found while building it: C#'s `double.NaN` has the
  sign bit set and Python's NaN does not, so a written NaN's bytes differ between the languages;
  shared write vectors use only infinities. Python 2539 passed, 2 skipped; .NET 2055
  passed; conformance 1286/1286 in both. Version 2026.11.13.78.
- 2026-11-13: FSK in the link (ADR 0057): `modulation` `"fsk2"` and `"fsk4"` (index 1) run
  `fsk_modulate` through the same channel (AWGN signal power 1). The receiver finds the sample
  timing from the detector's largest tone energy over the whole stream, then the frame from the
  preamble's known tones at that phase, then runs `fsk_demod_noncoherent`. `ber_theory` is
  `fsk_ber_theory`; `frequency_offset_hz`, `phase_offset` and `evm` are now optional and none for
  FSK (C# `double?`, `Evm?`), and the link compare skips EVM for them. Gains are rejected with
  FSK, `sps` must be at least `M`. Found while building it: a preamble-only search often lands a
  sample early under noise (with continuous phase the energy one sample off is only a few
  percent lower), costing several times the errors, so the timing comes from the whole stream
  as in the PSK chain; offsets `delay` and `delay + 1` decide the same bits, so noisy FSK link
  configs keep `delay mod sps < sps − 1`. New link configs `fsk2_noiseless`, `fsk4_noiseless`,
  `fsk2_8db`, `fsk4_7db`. Python 2566 passed, 2 skipped; .NET 2082 passed; conformance
  1286/1286 in both. Version 2026.11.13.79.
- 2026-11-13: Unsigned SigMF sample types (ADR 0058): `u32`, `u16` (each with an order) and `u8`
  (none), real and complex, as offset binary: code `u` is `(u − 2^(b−1))/2^(b−1)`, so the same
  range and step as the signed type, and writing adds `2^(b−1)` to the signed code. C# flips the
  top bit of the signed code. Vector cases by hand (ends, mid-scale, the range edges, NaN) and a
  `receiver_cu8` recording replace the old "unsigned is rejected" cases; the cross-language file
  exchange now covers 28 datatypes. Python 2607 passed, 2 skipped; .NET 2123 passed; conformance
  1317/1317 in both. Version 2026.11.13.80.
- 2026-11-13: Lomb-Scargle periodogram (ADR 0059): `lomb_scargle(times, values, frequencies,
  center=True, normalization="standard")`, the classic form with Scargle's τ, real values,
  caller-given frequencies; `"power"` is `P`, `"standard"` is `2P/Σy²`. A sum of squared cosines
  or sines below `1e-12·N` drops its term (Nyquist of even samples). New generator
  `lomb_scargle.py` (23 cases): closed forms on even samples and, on uneven times, the
  least-squares sinusoid fit solved from its normal equations with no τ. Python 2641 passed,
  2 skipped; .NET 2155 passed; conformance 1340/1340 in both. Version 2026.11.13.82.
- 2026-11-13: OFDM modulate and demodulate (ADR 0060): `ofdm_modulate(symbols, nfft, cp_len,
  subcarriers=None)` and `ofdm_demodulate`, unitary DFT both ways, signed subcarrier indices
  (`−⌊N/2⌋ … N − 1 − ⌊N/2⌋`, filled in the order listed, default all ascending), cyclic prefix
  from the block's tail, whole blocks only. New generator `ofdm.py` (30 cases): blocks by hand,
  the definition as direct sums with cmath (no FFT), round trips, and the prefix dropped on
  samples that are not OFDM. Tests show a multipath channel within the prefix demodulates as one
  gain per subcarrier. Also from review: `lomb_scargle` now rejects strings of digits instead of
  converting them. Python 2685 passed, 2 skipped; .NET 2193 passed; conformance 1370/1370
  in both. Version 2026.11.13.83.
- 2026-11-13: SigMF annotations (ADR 0061): the metadata key `core:annotations`, a list of JSON
  objects, is written to the top-level `annotations` array and read back from it in file order;
  each needs an integer `core:sample_start` ≥ 0 and may have an integer `core:sample_count` ≥ 0,
  other fields kept as they are; the list must be sorted by start (rejected, not sorted, both
  ways); an empty or missing array gives no key. `annotations: null` and a global
  `core:annotations` are rejected on reading. The cross-language file exchange now carries two
  annotations. Both conformance runners compare a JSON list (an array holding a record, a string,
  a bool or null) element by element; the `files` generator gained 12 annotation cases and
  `foreign_ci16` now expects its annotation. Python 2711 passed, 2 skipped; .NET 2221
  passed; conformance 1382/1382 in both. Version 2026.11.13.85. (The first build of this, .84, failed: the C# report writer could not encode a list; fixed.)
- 2026-11-13: Lomb-Scargle false-alarm probability and frequency grid in both languages
  ([ADR 0062](adr/0062-lomb-scargle-significance.md)). `lomb_scargle_false_alarm` /
  `Spectral.LombScargleFalseAlarm` gives, for the standard normalization, the Beta survival
  `(1 − z)^((N − d)/2)` of white Gaussian noise (`d` 3 centered, 2 not; Scargle's exponential form
  is for a known noise variance, so not used) and `1 − (1 − P₁)^M` over `M` frequencies through
  log1p/expm1 (C# has its own Kahan forms). `lomb_scargle_frequencies` /
  `Spectral.LombScargleFrequencies` gives `k/(oversampling·T)` up to `N/(2T)` or a given maximum.
  New generator `lomb_scargle_fap.py` (30 cases, exact fractions); Monte Carlo tests check the
  survival on noise in both languages. Python 2760 passed, 2 skipped; .NET 2269 passed;
  conformance 1412/1412 in both. Version 2026.11.13.86.
- 2026-11-13: OFDM in the link ([ADR 0063](adr/0063-ofdm-link.md)): `modulation = "ofdm"`, Gray
  QPSK on `ofdm_subcarriers` [all but DC] of an `ofdm_nfft` [64] DFT with an `ofdm_cp_len` [16]
  prefix, `P` known preamble blocks. Receiver: van de Beek's prefix metric `|γ| − Φ` for timing
  within a block and the carrier offset, the known preamble samples for the block (the prefix
  ties one block early when the delay exceeds a block, found in testing), per-subcarrier least
  squares over the preamble, decision-directed common phase per block. Noise is defined per data
  subcarrier, so `ber_theory` is QPSK theory (exact channel knowledge; the estimate's loss,
  about `10·log10(1 + 1/P)` dB, bounds the tests). Phase noise, clock offset, loop gains and
  offsets of half a subcarrier or more are rejected. New link configs `ofdm_noiseless`
  (52 subcarriers) and `ofdm_6db`. Python 2785 passed, 2 skipped; .NET 2292 passed;
  conformance 1412/1412 in both. Version 2026.11.13.88 (.87 failed: the noiseless OFDM EVM is rounding error, about −299 dB, so its dB value and peak index differ between languages; the link compare now skips those two when both rms are ≤ 1e-9, docs/testing.md).
- 2026-11-13: Multipath in the OFDM link ([ADR 0064](adr/0064-link-multipath.md)):
  `multipath_delays` and `multipath_gains` (`[re, im]` pairs) run `multipath` first in the
  channel, with room after the frame for every echo; `"ofdm"` only, delays at most `⌊cp/2⌋`. The
  receiver backs its DFT windows off half a prefix from the timing estimate and takes the
  window shift's phase ramp out of `phase_offset`. `ber_theory` is the mean over subcarriers of
  QPSK theory at `|H_k|²·Eb/N₀`. Found in testing: the timing search stopped at the direct
  path's start until the echo room was added, and a BER bracket with 8 preamble blocks failed in
  C# because each run's channel estimate is shared by all its blocks (the tests use 64), and for
  the same reason the flat `ofdm_6db` EVM compare failed at 5.9 sd once the back-off moved the
  windows (its preamble is now 64 blocks too). The
  prefix's frequency estimate is slightly biased by the echo (noiseless: about 0.012 Hz of a
  62.5 Hz spacing). New link configs `ofdm_multipath_noiseless` and `ofdm_multipath_8db`.
  Python 2809 passed, 2 skipped; .NET 2311 passed; conformance 1412/1412 in both.
  Version 2026.11.13.92 (.89 to .91 failed on the lint and the two compares above).
- 2026-11-13: Phase noise and clock offset in the OFDM link
  ([ADR 0065](adr/0065-ofdm-phase-noise-clock.md)): `phase_noise_linewidth_hz`,
  `clock_offset_ppm` and `timing_loop_gains` are accepted for `"ofdm"` (`carrier_loop_gains` stay
  rejected: the block phase is its carrier loop). Every frame is followed by `⌊cp/2⌋` zeros, and
  the clock drift over the frame must fit in what is left of half the prefix after the delay
  spread. The receiver turns each preamble block's estimate to block 0's common phase before the
  average, then runs a per-block loop on the known preamble and then on decisions: the common
  phase `θ` every block and, with `timing_loop_gains`, a second-order loop on the window offset
  `τ` from the phase slope across subcarriers. `ber_theory` is unchanged. Found in testing: with
  a long preamble the prefix's small frequency error turned the averaged estimate more than π/4
  and the link locked a quadrant off (EVM² 2.5 instead of 0.05), and 0.5 Hz of phase noise did
  the same; the band-edge subcarrier `−N/2` cannot survive resampling, so clock-offset runs
  use guard subcarriers. New link configs `ofdm_clock_noiseless`, `ofdm_clock_6db` and
  `ofdm_phase_noise_6db` (52 subcarriers). Python 2817 passed, 2 skipped; .NET 2320 passed;
  conformance 1412/1412 in both. Version 2026.11.13.93.
- 2026-11-13: LMS equalizer ([ADR 0066](adr/0066-lms-equalizer.md)): `lms_equalizer(samples,
  training, num_taps, step, *, samples_per_symbol=1, center=None, decision=None)` in `sync`
  (C# `Sync.LmsEqualizer`), normalized LMS with fractionally spaced taps that start as a unit
  impulse at `center`, trained on the given symbols and then, with `decision`, on the hard
  decisions of QPSK, 8-PSK, 16-QAM or 64-QAM; the result `Equalization` has the symbols, the
  errors and the final taps. New generator `equalizer.py` (18 cases: pass-through at step 0,
  one-tap inversion of a gain at step 1, zero input, the recurrence for each decision and
  spacing, rejects). Python 2854 passed, 2 skipped; .NET 2346 passed; conformance
  1430/1430 in both. Version 2026.11.13.94.
- 2026-11-13: the LMS equalizer in the single-carrier link ([ADR
  0067](adr/0067-link-equalizer.md)): `equalizer_taps` and `equalizer_step` [0.1] in the config;
  with them QPSK, 8-PSK, 16-QAM and 64-QAM take `multipath_delays`. The equalizer replaces the
  final derotation, fractionally spaced at 2 samples per symbol on the matched-filter output from
  the frame start, trained on the preamble and then decision-directed; the preamble no longer
  counts in the EVM and BER. `ber_theory` over multipath is the matched-filter bound (the energy
  the paths give one raised-cosine pulse). Measured 0.1–0.5 dB from the bound on a three-path
  channel; tests allow 1 dB. New link configs `qpsk_equalizer_noiseless`, `qpsk_multipath_6db`,
  `qam16_multipath_12db`. Python 2884 passed, 2 skipped; .NET 2376 passed; conformance
  1430/1430 in both. Version 2026.11.13.96.
- 2026-11-13: frame search in blocks ([ADR 0068](adr/0068-block-frame-search.md)): step 3 of the
  single-carrier receiver adds the magnitudes of the preamble correlation over blocks of
  `phase_block_symbols`, so a residual frequency error no longer turns a long preamble's sum
  through a cycle; with the default `P = B` it is the old search. On a strong-ISI channel at
  6 dB with a 1000-symbol preamble, 10 of 10 seeds now find the frame (4 of 10 missed). Review
  fix: with the equalizer, `preamble_symbols` must be below `num_symbols` (it raised from the
  EVM on an empty span). Python 2889 passed, 2 skipped; .NET 2381 passed; conformance
  1430/1430 in both. Version 2026.11.13.98.
- 2026-11-13: decision-feedback equalizer ([ADR
  0069](adr/0069-decision-feedback-equalizer.md)): `dfe_equalizer` / `Sync.DfeEqualizer`, the LMS
  equalizer plus feedback taps on the past references, one normalized update over both; with no
  feedback taps it is `lms_equalizer` exactly (the two share one implementation). Vectors in
  `vectors/cases/dfe.json` (14 cases, `generators/dfe.py`). On `1 + 0.95 z⁻¹` at N₀ = 0.01 its
  MSE is within 15% of the MMSE-DFE bound (closed form), a fifth of the MMSE linear bound. Python
  2910 passed, 2 skipped; .NET 2402 passed; conformance 1444/1444 in both. Version 2026.11.13.99.
- 2026-11-13: decision feedback and a preamble frequency in the link ([ADR
  0070](adr/0070-link-dfe-preamble-frequency.md)): `equalizer_feedback` runs step 7 as
  `dfe_equalizer`; with the equalizer the frequency is a least-squares line through the
  preamble's full blocks' phases (data-aided), as the blind estimators are about 1 Hz off through
  strong interference. Through an echo of 0.9 one symbol late, at QPSK 8 dB the BER falls from
  0.015 (linear) to 0.0002–0.0007 with two feedback taps, and at 16-QAM 14 dB from 0.34 to under
  0.0002; noiseless, all four modulations decode (64-QAM with a 2000-symbol preamble). Three link
  configs. 8-PSK through it at 12 dB still fails (Next). Python 2925 passed, 2 skipped; .NET
  2417 passed; conformance 1444/1444 in both. Version 2026.11.13.100.
- 2026-11-13: a data-aided coarse frequency with the link equalizer ([ADR
  0071](adr/0071-link-data-aided-coarse-frequency.md)): with `equalizer_taps` and a preamble of 2
  or more, step 2's `f₁` is the angle of the preamble's lag-1 symbol-step correlation at its
  peak over the start, which does not depend on the frequency (range ±R/2). Through the 0.9 echo
  8-PSK at 12 dB now decodes at offsets of 5, 37 and −120 Hz (BER 0.0001–0.001; before, half the
  runs failed with the estimate 31.25 Hz off). One more link config. Python 2927 passed, 2
  skipped; .NET 2421 passed; conformance 1444/1444 in both. Version 2026.11.13.101.
- 2026-11-13: a least-squares equalizer start ([ADR
  0072](adr/0072-least-squares-equalizer-start.md)): `dfe_least_squares` solves the forward and
  feedback taps on the training by elimination with partial pivoting on the normal equations
  (written out in the conventions); `lms_equalizer` and `dfe_equalizer` take `initial_taps` (and
  `initial_feedback`); the link's `equalizer_start = "least_squares"` starts step 7 there.
  Through the 0.9 echo with a 100-symbol preamble 16-QAM at 14 dB falls from a BER of 0.37–0.46
  to 0.002–0.007; QPSK at 8 dB still fails in two of three runs from the frequency (Next). New
  vector suite `dfe_least_squares` (12 cases, by-hand closed forms), initial-start cases in
  `equalizer` and `dfe`, one more link config. Python 2963 passed, 2 skipped; .NET 2448
  passed; conformance 1464/1464 in both. Version 2026.11.13.103.
- 2026-11-13: a phase loop inside the equalizer ([ADR 0073](adr/0073-equalizer-phase-loop.md)):
  `dfe_equalizer`'s `phase_loop_gains = (kp, ki)` turns the forward part by a second-order
  decision-directed loop, the forward taps adapting in their own frame and the feedback unturned;
  the link's `equalizer_loop_gains` passes it through. Through the 0.9 echo with the
  least-squares start and a 100-symbol preamble, at `(0.02, 0.0001)` QPSK at 8 dB, 16-QAM at
  14 dB and 8-PSK at 12 dB all decode (BER ≤ 0.0013, from up to 0.55); noiseless 16-QAM goes
  from 4574 bit errors to none. Loop cases in the `dfe` vectors, one more link config. Python
  2983 passed, 2 skipped; .NET 2463 passed; conformance 1470/1470 in both. Version 2026.11.13.104.
- 2026-11-13: a blind equalizer ([ADR 0074](adr/0074-constant-modulus-equalizer.md)):
  `cma_equalizer(samples, num_taps, step, *, samples_per_symbol=1, center=None, modulus=1.0,
  initial_taps=None)` (C# `Sync.CmaEqualizer`), the normalized constant-modulus algorithm with
  the LMS equalizer's regressor, start and spacing, and no training. Through a mild three-tap
  channel turned 0.7 rad it opens the eye with no known symbols (QPSK 0.006, 16-QAM 0.013 after
  the best rotation), and its taps, turned by the π/2 the known symbols give, start a
  decision-directed LMS that does as well as one trained on every symbol. The link does not use
  it. Vector suite `cma` (20 cases, 3 by hand). Python 3011 passed, 2 skipped; .NET 2488
  passed; conformance 1490/1490 in both. Version 2026.11.13.105.
- 2026-11-13: pilots that correct the phase loop's cycle slips ([ADR
  0075](adr/0075-pilot-slip-correction.md)): `dfe_equalizer` gains `pilots`, `pilot_interval`
  and `slip_window=2` (C# the same, PascalCase). Every `K`-th output after the training is a known
  symbol: the reference there, and every `slip_window` pilots the loop's phase steps by the
  multiple of π/2 (π/4 for 8-PSK) nearest their summed rotation. The link gains
  `pilot_interval` (only with `equalizer_loop_gains`); pilots do not count in the errors. 8-PSK
  at 12 dB with a 100-symbol preamble, seeds 80–89: six of ten slip to 0.32–0.63 without
  pilots, all under 0.01 with one in 20 (the good runs unchanged). The same holds with C#'s
  noise. ADR 0073's "every run" claim corrected (seed 84 slips at its gains). Pilot cases in the
  `dfe` vectors (one by hand), one more link config. Python 3036 passed, 2 skipped; .NET
  2505 passed; conformance 1501/1501 in both. Version 2026.11.13.106.
- 2026-11-13: an RLS equalizer ([ADR 0076](adr/0076-rls-equalizer.md)):
  `rls_equalizer(samples, training, num_taps, forgetting, *, delta=0.01, samples_per_symbol=1,
  center=None, decision=None, initial_taps=None)` (C# `Sync.RlsEqualizer`), exponentially
  weighted recursive least squares with the LMS equalizer's regressor, start, spacing, training
  and decisions. On a zero at radius 0.9 (QPSK, 15 taps) it is at 0.06 mean square error by
  symbols 25–49, where normalized LMS is at 0.32, and at 0.03 after 400, where LMS is at 0.11.
  Its taps are the weighted, regularized least-squares solution, checked against a direct solve
  in the generator and both test suites. The link does not use it yet. Vector suite `rls` (21
  cases, 3 by hand). The architecture's Sync row now lists ADRs 0072–0076. Python 3069
  passed, 2 skipped; .NET 2532 passed; conformance 1522/1522 in both. Version 2026.11.13.107.
- 2026-11-13: RLS training for the decision-feedback equalizer and the link ([ADR
  0077](adr/0077-rls-decision-feedback.md)): `dfe_equalizer(..., forgetting=None, delta=0.01)`
  (C# `forgetting`, `delta`) trains the forward and feedback taps by RLS over the rotated forward
  samples and the past references, with the phase loop, pilots, training and starts unchanged;
  the link's `equalizer_forgetting` passes it. On the two-path echo with a 100-symbol preamble and
  a 5 Hz offset, LMS from the impulse fails on every seed for 16-QAM (0.24–0.45) and 8-PSK (0.32),
  RLS (λ 0.999) gets 0.0001–0.0027; for 8-PSK it also beats the least-squares start, which fails
  on 4 of 6 seeds. Forward-only RLS (ADR 0076) barely helps the link. Vector suite `dfe` now 45
  cases (two checked against the direct least-squares solve); link config `qpsk_dfe_rls_8db`.
  Python 3085 passed, 2 skipped; .NET 2549 passed; conformance 1532/1532 in both. Version
  2026.11.13.108.
- 2026-11-13: multitaper spectra ([ADR 0078](adr/0078-multitaper.md)):
  `dpss_tapers(length, half_bandwidth, num_tapers=None)` (C# `Spectral.DpssTapers`) returns a
  `TaperSet` of the Slepian tapers and their concentrations, by Sturm bisection and inverse
  iteration on the commuting tridiagonal matrix (no dense eigen-solver, so no dependency);
  `multitaper_psd(samples, sample_rate, half_bandwidth, *, num_tapers=None, one_sided=None,
  nfft=None)` (C# `Spectral.MultitaperPsd`) averages the tapered periodograms of the whole input
  in the Welch scaling and folding. The tapers meet the sinc eigen-equation to 1e-11 up to N = 512;
  4096 samples take about 0.5 s in Python. Measured: the first taper at NW 4 leaks 4e-11 of the
  peak from 6 bins out where Hann leaks 1e-6, but all seven tapers leak near the rectangular
  window, which is what the adaptive weights (Next) are for. Vector suite `multitaper` (22 cases:
  tapers by cyclic Jacobi in the generator, each checked against the sinc eigen-equation, two by
  hand). The result type is `TaperSet`, not `Tapers`: a C# record cannot have a property of its
  own name. Python 3118 passed, 2 skipped; .NET 2582 passed; conformance 1554/1554 in both.
  Version 2026.11.13.109.
- 2026-11-13: Thomson's adaptive weights for the multitaper PSD ([ADR
  0079](adr/0079-adaptive-multitaper.md)): `multitaper_psd(..., adaptive=True)` (C# `adaptive:
  true`) combines the eigenspectra bin by bin with the weights
  `λ_j / (λ_j S + (1 − λ_j) σ²/fs)²`, iterated from the mean of the first two to a per-bin fixed
  point (`1e-10`, at most 1000 repeats). On a tone at N 1024, NW 4 with seven tapers the leakage
  6 bins out falls from 3.6e-3 of the peak to 5.8e-7, and 50 bins out from 4.2e-5 to 2.9e-12;
  white noise keeps its level. ADR 0078's context now says the plain average leaks near the
  rectangular window rather than claiming less leakage than any window. Vector suite
  `multitaper` now 28 cases (3 by hand). Python 3127 passed, 2 skipped; .NET 2591 passed;
  conformance 1560/1560 in both. Version 2026.11.13.110.
- 2026-11-13: review of the multitaper code for size: the concentrations were an `O(N²)`
  autocorrelation per taper (93 s at N 65536 in Python, `np.correlate` not using an FFT), and
  adaptive mode always needs them. Both languages now take each autocorrelation by an FFT of
  length `2N`, within 2e-15 of the direct sum; N 65536 with seven tapers now takes about 6 s in
  Python, nearly all in the pure-Python taper solve (linear in N). Python 3127 passed, 2
  skipped; .NET 2591 passed; conformance 1560/1560 in both. Version 2026.11.13.111.
- 2026-11-13: Thomson's harmonic F-test ([ADR 0080](adr/0080-harmonic-f-test.md)):
  `harmonic_f_test(samples, sample_rate, half_bandwidth, *, num_tapers, nfft)` → `HarmonicFTest`
  (C# `Spectral.HarmonicFTest` → `HarmonicFTestResult`) regresses each bin's tapered DFTs on the
  tapers' sums. The result has the line amplitude `μ`, an F statistic with 2 and `2K − 2` degrees
  of freedom, and its exact p-value `(1 + F/(K − 1))^−(K−1)`. Real input gives bins 0 … fs/2;
  complex input gives the two-sided axis. `K ≥ 2`. Under white noise the p-values are uniform
  (5.2% below 0.05 over 20 × 1024 bins), and a 0.3 cosine in unit noise at N 4096 is the smallest
  p-value at about 1e-7. Vector suite `multitaper` now 39 cases (2 more by hand: N = 2 and all
  zeros). Python 3143 passed, 2 skipped; .NET 2607 passed; conformance 1571/1571 in both.
  Version 2026.11.13.112.
- 2026-11-13: generalized Lomb-Scargle ([ADR 0081](adr/0081-generalized-lomb-scargle.md)):
  `generalized_lomb_scargle(times, values, frequencies, *, uncertainties, normalization)` (C#
  `Spectral.GeneralizedLombScargle`) is Zechmeister & Kürster's weighted fit of
  `a cos ωt + b sin ωt + c` with weights `1/σ²`. It uses their τ, so the centered cross term
  vanishes. Standard gives `(χ²₀ − χ²)/χ²₀`; power gives `½(χ²₀ − χ²)`. On samples bunched at a
  cosine's peaks it gives 1 where the classic centered form gives 0.96. With unit σ on even
  samples at bins it equals the classic form within 1e-12. New vector suite
  `generalized_lomb_scargle` (23 cases, 7 by hand), from a stdlib generator solving the weighted
  3×3 normal equations with no τ. Python 3171 passed, 2 skipped; .NET 2635 passed;
  conformance 1594/1594 in both. Version 2026.11.13.113.
- 2026-11-13: Lomb-Scargle false-alarm level
  ([ADR 0082](adr/0082-lomb-scargle-false-alarm-level.md)):
  `lomb_scargle_false_alarm_level(probability, num_samples, *, num_frequencies, center)` (C#
  `Spectral.LombScargleFalseAlarmLevel`) inverts the false-alarm probability in closed form,
  using `log1p`/`expm1` so tiny `p` and large `M` keep full precision. With `center` it also
  serves the generalized form: in a Monte Carlo of weighted Gaussian noise at one frequency, the
  10% level is exceeded at the stated rate in both languages. `lomb_scargle_fap` gains 22 cases:
  6 by hand, 10 round trips through the exact-fraction table, 6 errors (52 in all). Lesson: a
  round trip near `z = 1` is only as good as `1 − z` after rounding `z`, so those cases get a
  looser tolerance. Python 3197 passed, 2 skipped; .NET 2661 passed; conformance
  1616/1616 in both. Version 2026.11.13.114.
- 2026-11-13: multitaper line removal ([ADR 0083](adr/0083-multitaper-line-removal.md)):
  `multitaper_line_removal(samples, sample_rate, half_bandwidth, *, probability, num_tapers,
  one_sided, nfft, adaptive)` (C# `Spectral.MultitaperLineRemoval`, real and complex, returning
  `LineRemovalResult<T>`) is Thomson's reshaping. A bin is a line when its F-test `p` is below
  `probability` (default `1/N`) and its `F` peaks within the half-bandwidth. Each line comes off
  the samples, which is the same as subtracting `μ·V_k(f − f₀)` from every eigencoefficient
  (tested against the DPSS DFTs directly). The PSD is then recomputed with every
  `multitaper_psd` option. The F-test's peak rule keeps one line per peak when padding puts
  several bins over the threshold. `multitaper` gains 12 cases (7 removal, 3 of them by hand:
  pure complex tone, DC, Nyquist; 5 errors), all at least 1.7× from their thresholds. Lesson: at
  the default `1/N` a spectrum expects about one noise line, so tests that count lines set a
  strict probability. The vectors README now states the generator naming rule instead of a list that had fallen behind. Python 3214 passed, 2 skipped; .NET 2678 passed; conformance
  1628/1628 in both. Version 2026.11.13.115.
- 2026-11-14: frequency-sampling FIR design ([ADR 0084](adr/0084-frequency-sampling-fir.md)):
  `fir_frequency_sampling(num_taps, frequencies, gains, sample_rate, window, beta, num_points)`
  (C# `Dsp.FirFrequencySampling`) samples a piecewise-linear gain on `K` points from 0 to fs/2.
  It gives the samples a symmetric filter's linear phase, takes the inverse `2(K − 1)`-point DFT,
  windows the result, and averages the taps with their reverse so they are exactly symmetric.
  There is no rescaling, so a flat gain gives the unit impulse. Even `num_taps` needs zero gain
  at fs/2. New `frequency_sampling` suite of 25 cases: 4 by hand, 7 from the generator's direct
  cosine sums, 14 errors. Lesson: averaging the taps with their reverse before the window did
  not give exact symmetry, because a computed window is only symmetric to round-off. The tests
  caught it, and the averaging now comes last. Python 3244 passed, 2 skipped; .NET 2708
  passed; conformance 1653/1653 in both. Version 2026.11.14.0.
- 2026-11-14: antisymmetric frequency sampling ([ADR 0085](adr/0085-antisymmetric-frequency-sampling.md)):
  `kind` on `fir_frequency_sampling` (`"filter"`, `"hilbert"`, `"differentiator"`), with
  equiripple design's amplitude convention. The grid samples get an extra `−j`, so the taps are a
  sine sum, and they are made exactly antisymmetric after the window. A Hilbert design needs zero
  gain at 0, and an odd length needs zero gain at fs/2 for both kinds. C# `EquirippleKind` is
  renamed `FirKind`, shared by both designs. 11 new cases: 3 by hand (the 3-tap and 2-tap
  differentiators, the 2-tap Hilbert), 4 from the generator's direct sine sums, 4 errors.
  Python 3259 passed, 2 skipped; .NET 2723 passed; conformance 1664/1664 in both.
  Version 2026.11.14.1.
- 2026-11-14: antisymmetric least-squares design ([ADR 0086](adr/0086-antisymmetric-least-squares.md)):
  `kind` on `fir_least_squares` (`"filter"`, `"hilbert"`, `"differentiator"`), so all three
  band-target FIR designs share it. Sine bases replace the cosines, and the normal equations use
  closed-form sine moments up to `ν²`, because the differentiator's target `−2πν·D(ν)` is
  quadratic. The weight is plain, unlike equiripple's relative differentiator weight, whose
  integrals have no closed form. Targets the type cannot meet (at 0, and at fs/2 for odd `N`) are
  part of the error, as for type II filters. 9 new cases: 2 by hand (the 2-tap Hilbert
  `[−2/π, 2/π]`, the 3-tap differentiator `[1, 0, −1]`), 5 from the generator's Simpson-checked
  integrals solved exactly, 2 errors. Python 3274 passed, 2 skipped; .NET 2738 passed;
  conformance 1673/1673 in both. Version 2026.11.14.2.
- 2026-11-14: half-precision SigMF samples ([ADR 0087](adr/0087-half-float-samples.md)):
  `rf16_le`, `rf16_be`, `cf16_le` and `cf16_be` in `encode_samples`, `decode_samples`,
  `write_sigmf` and `read_sigmf`, as IEEE binary16 (NumPy `float16`, C# `Half`). Writing rounds
  once from the double, never through binary32, which could land on a different value. Beyond
  65504 is ±inf, as for `f32`, and subnormals are kept. The files generator packs binary16 by hand
  with exact rational rounding and checks each value against `struct`'s `e` format. 14 new cases:
  the round-trip set for the four types, by-hand cases for the limits, ties, overflow,
  subnormals and a double-rounding trap, and a big-endian `cf16` recording. The `half_float`
  rejection recording became `wide_int` (`ri64_le`). A new test round-trips every non-NaN binary16
  pattern in both languages. Lesson: the Python round-trip test measured the complex error as
  `|y − x|` and C# measured each part, so `f16`'s coarser step failed only in Python. Both now
  measure each part. Python 3294 passed, 2 skipped; .NET 2758 passed; conformance
  1687/1687 in both. Version 2026.11.14.3.
- 2026-11-14: more `.npy` dtypes on read ([ADR 0088](adr/0088-npy-read-dtypes.md)): `read_npy`
  takes `'<f8'`, `'>f8'`, `'<f4'`, `'>f4'`, `'<f2'`, `'>f2'`, `'<c16'`, `'>c16'`, `'<c8'` and
  `'>c8'`, widened exactly to `float64` / `complex128`. `=` and `|` byte orders, long doubles
  (`'<f16'`) and integers are still rejected, and `write_npy` is unchanged. The npy generator packs
  the data with `struct` (`d`, `f`, `e`, both byte orders) from values each type holds exactly. 13
  new cases: 9 files to read, and 7 rejections that replace the old `big_endian` and `float32`
  rejections. The C# runner now picks `Complex` for any `c8` or `c16` descr. New tests read
  `numpy.save` output of every dtype in Python, and hand-packed files in C#. Lesson: a
  test value has to be exact in the narrowest type. 1000.25 is not exact in binary16, and only
  C#, which compares with the original value, caught it. Python 3322 passed, 2 skipped;
  .NET 2779 passed; conformance 1700/1700 in both. Version 2026.11.14.4.
- 2026-11-14: NumPy `.npz` archives (ADR 0089): `write_npz(path, arrays)` and `read_npz(path)`
  (C# `WriteNpz`, `ReadNpz`, the latter returning an `OrderedDictionary<string, Array>`). Each member
  is a `.npy` file as `write_npy` writes and `read_npy` reads, keyed by its name without `.npy`, in
  archive order. Writing stores members uncompressed with a fixed 1980-01-01 timestamp, so the bytes
  are the same in both languages and `numpy.load` reads them. Reading takes stored and deflated
  members, ZIP64 extra fields (which `numpy.savez` always writes), data descriptors, UTF-8 names and
  archive comments. It rejects encryption, other methods (bzip2, LZMA, Deflate64), multi-disk and
  ZIP64-end archives, a bad CRC-32, a wrong size, non-`.npy` members and duplicate keys. Both
  languages parse the ZIP by hand (CRC-32 and inflate from `zlib` and `System.IO.Compression`)
  rather than through `zipfile` or `ZipArchive`, because the two accept different methods. New
  generator `npz.py` (43 cases, 33 archives, stdlib `struct` and `zlib` only); its good archives
  were also checked with `numpy.load`. Lesson: an archive comment that holds the end signature is
  ambiguous, and `zipfile` takes the wrong record, so it was not kept as a good case.
  Python 3382 passed, 2 skipped; .NET 2837 passed; conformance 1743/1743 in both. Version
  2026.11.14.5.
- 2026-11-14: integer `.npy` dtypes on read (ADR 0090): `read_npy`, and so `read_npz`, also
  read `'|i1'`, `'|u1'` and `<`/`>` `i2`, `u2`, `i4`, `u4`, `i8`, `u8` as `float64` values with
  no scaling. 64-bit values beyond 2^53 round to the nearest double, ties to even. A one-byte
  integer must use `|`, as NumPy writes it. Booleans and `=` stay rejected. Generator `npy.py`
  gained 16 good integer cases (each width and byte order, from `struct`, plus two cases rounded
  by hand) and 6 bad ones, all checked against `numpy.load`; `npz.py`'s bad member is now a
  boolean array. Lesson: a NumPy test that concatenates a `uint64` maximum with an `int64` array
  silently goes through `float64`; build the array in its own dtype.
  Python 3422 passed, 2 skipped; .NET 2873 passed; conformance 1764/1764 in both. Version
  2026.11.14.6.
- 2026-11-14: WAV `LIST`/`INFO` text tags (ADR 0091): `read_wav_info(path)` (C# `ReadWavInfo`)
  returns the tags of every `LIST`/`INFO` chunk in file order as an ordered mapping of ID to text,
  decoded byte for byte as Latin-1, each text up to its first NUL; `write_wav` (both C# overloads)
  takes an optional `info` and writes a `LIST`/`INFO` chunk after `data`, with IDs of four `A`–`Z`
  or `0`–`9` characters and printable ASCII texts. No or empty `info` writes the same bytes as
  before, and `read_wav` still ignores the tags. Duplicate IDs and chunks running past their
  container are rejected; a walk ends when fewer than 8 bytes are left, so missing final pad
  bytes are fine. Generator `wav.py` gained 7 good and 9 bad write cases and 15 good and 8 bad
  read files, the tagged PCM files checked with the `wave` module.
  Python 3491 passed, 2 skipped; .NET 2938 passed; conformance 1803/1803 in both. Version
  2026.11.14.7.
- 2026-11-14: 2-D `.npy` arrays (ADR 0092): `read_npy_2d(path)` (C# `ReadNpy2D<T>`, a `T[,]`)
  reads a `.npy` of shape `(rows, columns)` in either `fortran_order`, with every dtype
  `read_npy` reads, and returns it in C order; `write_npy` (C# `WriteNpy(path, double[,])` and
  `WriteNpy(path, Complex[,])`) writes a 2-D array in C order, byte for byte what `numpy.save`
  writes. Zero rows or columns are allowed; each dimension is at most 2147483591, the largest
  .NET allocates for a rectangular array (2^31 − 1 throws there, found by the C# tests).
  `read_npy` and `read_npy_2d` each reject the other's files; `.npz` stays 1-D. Generator
  `npy.py` gained 6 write cases and 11 good and 8 bad `m2_*.npy` read files, all cross-checked
  with `numpy.save` and `numpy.load`.
  Python 3566 passed, 2 skipped; .NET 2979 passed; conformance 1828/1828 in both. Version
  2026.11.14.8.
- 2026-11-14: 2-D `.npz` members (ADR 0093): `read_npz` returns each member at its own
  dimensions, a 2-D member read as `read_npy_2d` reads a file (C#: a `double[,]` or `Complex[,]`
  in the `OrderedDictionary<string, Array>`), so one archive may mix 1-D and 2-D members; 0-D
  and 3-D members are still rejected. `write_npz` takes 2-D values too (C# `double[,]` and
  `Complex[,]`), each member the bytes `write_npy` writes. No separate `read_npz_2d`: the C#
  values already carry their rank. Generator `npz.py` gained 3 write cases and 4 good and 4 bad
  read archives, cross-checked with `numpy.load`.
  Python 3587 passed, 2 skipped; .NET 2993 passed; conformance 1839/1839 in both. Version
  2026.11.14.9.
- 2026-11-14: WAV cue points (ADR 0094): `read_wav_cues(path)` (C# `ReadWavCues`) returns each
  point of the `cue ` chunk in its order as (position in frames, label), the labels from `labl`
  subchunks of every `LIST`/`adtl` chunk matched by cue ID, `""` for none. `write_wav` takes an
  optional `cues` of (position, label) pairs, positions 0 to the length, labels printable ASCII,
  and writes a `cue ` chunk (IDs 1, 2, …, play order = sample offset) and a `LIST`/`adtl` for
  the non-empty labels after `data`, before `LIST`/`INFO`. Rejected on read: two `cue ` chunks,
  a size that is not 4 + 24 × count, a point outside the `data` chunk (`wavl` lists), a
  duplicate ID, a position past the frames, a label with no point or a second label. Cue IDs
  are not exposed. Generator `wav.py` gained 12 write cases and 34 read files, the PCM ones
  cross-checked with the `wave` module.
  Python 3658 passed, 2 skipped; .NET 3053 passed; conformance 1885/1885 in both. Version
  2026.11.14.10.
- 2026-11-14: WAV cue regions (ADR 0095): a cue is now (position, length, label), length 0 for a
  plain point, in `read_wav_cues` and `write_wav` (C# `(long Position, long Length, string
  Label)`), replacing ADR 0094's pairs. A non-zero length is written as a 20-byte `ltxt`
  (purpose `rgn `, locale fields 0, no text) after the cue's `labl`; on read an `ltxt` gives the
  length, its purpose, locale and text ignored. Rejected: an `ltxt` under 20 bytes, one with no
  cue point or a second for one ID, and a region running past the frames (on write too). The
  generator's `note_ltxt_skipped` file became `note_skipped`, since `ltxt` is now read; it
  gained 6 write cases and 11 read files.
  Python 3681 passed, 2 skipped; .NET 3075 passed; conformance 1902/1902 in both. Version
  2026.11.14.11.
- 2026-11-14: Multi-channel SigMF recordings (ADR 0096): `read_sigmf_channels` /
  `write_sigmf_channels` (C# `ReadSigmfChannels`, `WriteSigmfChannels`) read and write one signal
  per channel, samples interleaved frame by frame; `core:num_channels` an integer from 1 to
  65535 (`MAX_CHANNELS` / `MaxChannels`). Every channel shares the rate, frequency, time origin,
  units, impedance and metadata (each its own copy); writing builds each channel's metadata file
  and rejects channels whose files differ, or of mixed kind or length. `read_sigmf` still takes
  one channel and now names `read_sigmf_channels` when refusing more; one channel gives the
  `write_sigmf` files byte for byte. The files generator gained 11 recordings (3 multi-channel,
  7 bad channel counts or frames, an explicit `core:num_channels: 1`) and 16 cases.
  Python 3717 passed, 2 skipped; .NET 3113 passed; conformance 1918/1918 in both. Version
  2026.11.14.12.
- 2026-11-14: Multi-capture SigMF recordings (ADR 0097): `read_sigmf_captures` (C#
  `ReadSigmfCaptures`) reads a one-channel recording as one signal per capture, from its
  `core:sample_start` to the next capture's, each with its capture's `core:frequency` and the
  recording's time origin plus start over rate. Each annotation goes to the last segment starting
  at or before it, its start rebased; a segment with none has no annotations key. Starts must be
  integers (not bools or floats), the first 0, strictly increasing and not past the samples (one
  at the end is an empty segment); no captures is one segment at frequency 0. `read_sigmf` still
  rejects differing frequencies and now names the new reader. Writing captures is not built. The
  files generator gained 11 recordings (2 good, 9 bad) and 16 cases.
  Python 3750 passed, 2 skipped; .NET 3147 passed; conformance 1934/1934 in both. Version
  2026.11.15.0.
- 2026-11-15: Baluev false-alarm probability (ADR 0098): `lomb_scargle_false_alarm_baluev(power,
  times, max_frequency, center=True)` (C# `Spectral.LombScargleFalseAlarmBaluev`) estimates, for
  the standard normalization, the chance that white noise exceeds `z` anywhere up to `f_max`. It
  uses Baluev's (2008) alias-free form `1 − (1 − P₁)·e^(−τ)`, where `τ` comes from the variance of
  the times, so no count of independent frequencies is needed. The gamma ratio uses an exact
  recurrence, so neither language needs a log-gamma. It is within a few ε of the exact rational
  product at `N = 2·10⁴`, where `math.lgamma` is off by 1.5e-11. The `lomb_scargle_fap.py`
  generator gained 18 cases (one by hand at `N = 4`, the rest from `math.lgamma`). Monte Carlo
  tests in both languages check a 100-frequency grid search on uneven times.
  Python 3792 passed, 2 skipped; .NET 3180 passed; conformance 1952/1952 in both. Version
  2026.11.15.1.
- 2026-11-15: Baluev false-alarm level (ADR 0099): `lomb_scargle_false_alarm_level_baluev(
  probability, times, max_frequency, center=True)` (C# `Spectral.LombScargleFalseAlarmLevelBaluev`)
  inverts the Baluev probability by bisection on `[0, 1]` until the midpoint stops moving, with the
  same steps in both languages. Both functions now share one checked setup and one core. `F` is
  not quite monotone near 1 and at `N = d + 1`, so the level is defined as the crossing bisection
  finds; `p = 1` gives 0 directly. The generator gained 14 cases (round trips through its own
  `math.lgamma` route, the ends, an `N = 4` case by hand, and rejects).
  Python 3820 passed, 2 skipped; .NET 3207 passed; conformance 1966/1966 in both. Version
  2026.11.15.2.
- 2026-11-15: writing multi-capture SigMF recordings (ADR 0100): `write_sigmf_captures(path,
  segments, datatype=None)` (C# `SignalFiles.WriteSigmfCaptures`) joins signals of one kind into
  one recording, one capture per segment, each with its own center frequency. Each later time
  origin must be exactly the first's plus `start / sample_rate`, the expression the reader uses,
  so a `read_sigmf_captures` result writes back to the same bytes; anything else is rejected
  rather than rounded. Everything else must be identical, only the last segment may be empty, and
  annotations move up by the segment's start (in every segment but the last, each must start
  inside it). One segment gives the `write_sigmf` files. The expected metadata is written out by
  hand in the tests of both languages.
  Python 3837 passed, 2 skipped; .NET 3222 passed; conformance 1966/1966 in both. Version
  2026.11.15.3.
- 2026-11-15: Lomb-Scargle bootstrap (ADR 0101): `lomb_scargle_bootstrap(times, values,
  frequencies, draws, *, seed, center=True)` (C# `Spectral.LombScargleBootstrap`, with an `int` or
  `Random` seed) returns each draw's highest standard periodogram value. A draw resamples the
  values with replacement at the original times. A draw that cannot be normalized gives 0. The
  random streams differ between languages. So the generator has only seed-independent cases (a
  constant uncentered series, from its own least-squares fit) and rejects, 7 in all. Tests in
  both languages check the peaks on Gaussian noise against the Baluev estimate, and that a strong
  tone is above every draw.
  Python 3856 passed, 2 skipped; .NET 3242 passed; conformance 1973/1973 in both. Version
  2026.11.15.4.
- 2026-11-16: sample clock drift (ADR 0102): `clock_drift(samples, ppm_start, ppm_end, *,
  half_width=16)` (C# `Channel.ClockDrift`), a clock offset linear in input time from `ppm_start`
  at the first sample to `ppm_end` at the last. The read positions follow the recurrence
  `t_{n+1} = r + (1 + d)·t_n`, computed in closed form as `r·expm1(n·log1p(d))/d` so a small `d`
  keeps its digits. Equal offsets give `clock_offset` bit for bit. The generator runs the
  recurrence in exact rationals and reads with its own kernel; the output length of one case is
  worked by hand. 15 vectors.
  Python 3886 passed, 2 skipped; .NET 3269 passed; conformance 1988/1988 in both. Version
  2026.11.16.0.
- 2026-11-16: multiterm Lomb-Scargle (ADR 0103): `lomb_scargle_multiterm(times, values,
  frequencies, terms, *, uncertainties=None, normalization="standard")` (C#
  `Spectral.LombScargleMultiterm`) fits a constant and `terms` harmonics at each frequency, with
  weights. It is solved by modified Gram-Schmidt on weighted, centered columns in a fixed order,
  dropping a column the earlier ones already span, below the ADR 0081 threshold. `terms = 1` is
  the generalized form to rounding. The generator solves the uncentered normal equations in
  exact rationals. A square wave on eight samples is worked by hand from its DFT: one term
  explains `(1 + √2/2)/2`, three explain all of it. The standard form rejects equal values
  outright, because weights that do not sum to exactly 1 could leave a tiny scatter. 22 vectors.
  Python 3929 passed, 2 skipped; .NET 3305 passed; conformance 2010/2010 in both. Version
  2026.11.16.1.
- 2026-11-16: sample clock jitter (ADR 0104): `clock_jitter(samples, rms, *, seed,
  half_width=16)` (C# `Channel.ClockJitter`, with an `int` or `Random` seed) reads each sample at
  `n + rms·gₙ` through the fractional delay kernel, white Gaussian jitter of up to half a sample.
  The streams differ between languages, so the 8 vectors are the seed-independent ones
  (`rms = 0`, empty input, rejects). Tests in both languages check a tone's error power against
  `2(1 − e^{−(2πf·rms)²/2})` and that the recovered offsets are white with the given spread.
  Python 3949 passed, 2 skipped; .NET 3324 passed; conformance 2018/2018 in both. Version
  2026.11.16.2.
- 2026-11-16: noise figure by the Y-factor method (ADR 0105): `noise_figure_y_factor(hot_power,
  cold_power, enr_db, *, cold_temperature=290.0)` (C# `Measurements.NoiseFigureYFactor`) returns
  a `NoiseFigure` with Y, F, the noise figure in dB and the noise temperature, from
  `F = (ENR − Y·(T_c/T₀ − 1))/(Y − 1)`, `T₀ = 290 K`, so a cold load away from `T₀` is handled.
  A non-positive F is rejected; `0 < F < 1` is returned. The vectors are hand derivations; the
  tests also measure a simulated device of known noise temperature.
  Python 4028 passed, 2 skipped; .NET 3402 passed; conformance 2040/2040 in both. Version
  2026.11.16.3.
- 2026-11-16: cascaded noise figure (ADR 0106): `noise_figure_cascade(noise_figures_db,
  gains_db)` (C# `Measurements.NoiseFigureCascade`) applies Friis' formula to matched stages in
  chain order and returns a `CascadeNoiseFigure`: F, NF, noise temperature, total gain and each
  stage's term. Losses are stages with negative gain; a noise figure below 0 dB is rejected. The
  vectors are hand derivations, including a 6 dB loss before a 2 dB amplifier giving 8 dB.
  Python 4052 passed, 2 skipped; .NET 3427 passed; conformance 2053/2053 in both. Version
  2026.11.16.4.
- 2026-11-16: two-tone intermodulation (ADR 0107): `two_tone_imd(samples, sample_rate, f1, f2,
  *, window, beta, width)` (C# `Measurements.TwoToneImd`, real and complex) groups DC, the two
  tones and the products `2f₁ − f₂` and `2f₂ − f₁` (aliased) on the tone metrics' spectrum and
  returns their powers, each product's dBc to the mean tone power, and the intercept from the
  worse product, `ip3_db = 10·log10 P_t − worst/2`. A group landing on one already claimed is
  rejected. The vectors are a cubic nonlinearity expanded by hand, real and complex, on coherent
  tones; the tests check the small-drive intercept `A² = 4/(3|a₃|)`.
  Python 4076 passed, 2 skipped; .NET 3451 passed; conformance 2066/2066 in both. Version
  2026.11.16.5.
- 2026-11-16: single-sideband phase noise (ADR 0108): `phase_noise_ssb(samples, sample_rate,
  offsets, *, carrier, nperseg, window, beta, width)` (C# `Measurements.PhaseNoiseSsb`, real and
  complex) reads `L(f)` in dBc/Hz from a Welch PSD: the carrier is the strongest bin (or the one
  at `carrier`) with the tone metrics' group, and `L` is the mean PSD of the two sidebands over
  the group's power. Offsets inside the group or past the spectrum are rejected; the complex
  spectrum's upper edge `fs/2` is excluded. The vectors are pure phase modulation expanded by
  Jacobi–Anger, `L = J_k²/(J_0²·ENBW)`, real and complex, one segment and several; the tests
  check Wiener phase noise against its discrete Lorentzian as a statistic.
  Python 4098 passed, 2 skipped; .NET 3472 passed; conformance 2082/2082 in both. Version
  2026.11.16.6.
- 2026-11-16: integrated phase noise (ADR 0109): `integrated_phase_noise(samples, sample_rate,
  f_lo, f_hi, *, carrier, nperseg, window, beta, width)` (C# `Measurements.IntegratedPhaseNoise`,
  real and complex) sums the PSD's whole bins with `f_lo ≤ |f − f_c| ≤ f_hi` on both sides over
  the carrier group's power (the carrier as for `phase_noise_ssb`, now shared code), and returns
  it in dBc, as the RMS phase `φ_rms` in radians and as the RMS jitter `φ_rms/(2π|f_c|)`. The
  vectors are pure phase modulation, `ratio = Σ J_k²/J_0²` over the lines in the band, real and
  complex; the tests check a small sine's `m/√2` and Wiener phase noise against the Lorentzian's
  arctan integral as a statistic.
  Python 4115 passed, 2 skipped; .NET 3489 passed; conformance 2092/2092 in both. Version
  2026.11.16.7.
- 2026-11-16: second-order intermodulation (ADR 0110): `two_tone_ip2(samples, sample_rate, f1,
  f2, *, window, beta, width)` (C# `Measurements.TwoToneIp2`, real and complex) groups the
  products `f₂ − f₁` and `f₁ + f₂` after DC and the tones, sharing `two_tone_imd`'s code, and
  returns `ip2_db = 10·log10 P_t − worst_imd_dbc`. The vectors are a square law expanded by hand
  on real tones (one sum folded) and `x + a₂|x|²` on complex tones, whose sum product is empty;
  the tests check the intercept `A_IP2 = 1/|a₂|` and that it does not move with drive.
  Python 4130 passed, 2 skipped; .NET 3504 passed; conformance 2101/2101 in both. Version
  2026.11.16.8.
- 2026-11-16: ACPR through an RRC channel filter (ADR 0111): `acpr_rrc(frequencies, psd, center,
  symbol_rate, alpha, offsets, *, span)` (C# `Spectral.AcprRrc`) weights each bin's power at its
  centre by the RRC's `|H|²`, peak 1, instead of a rectangle, and returns `acpr`'s result. Bins
  need no partial edges: the raised cosine's bin sum of a flat PSD is exactly the symbol rate
  whenever `R/Δ` is whole. The vectors work flat, stepped and single-line PSDs by hand (the
  taper's cosines cancelling in pairs); the tests check an RRC QPSK keeps `1 − α/4` of its power
  and white noise reads the same in every channel.
  Python 4175 passed, 2 skipped; .NET 3531 passed; conformance 2116/2116 in both. Version
  2026.11.16.9.
- 2026-11-16: gain compression (ADR 0112): `gain_compression(input_db, output_db, *,
  compression_db=1.0, linear_points=1)` (C# `Measurements.GainCompression`) takes a drive sweep's
  levels, takes the small-signal gain from the lowest steps and interpolates the compression
  point linearly in dB between steps (NaN when the sweep never gets there), with the output point
  and the saturated output. The vectors are piecewise sweeps with round points and the cubic's
  fundamental `a₁A + ¾a₃A³`; the tests find the textbook `A² = (4/3)(1 − 10^(−1/20))|a₁/a₃|`.
  Python 4204 passed, 2 skipped; .NET 3552 passed; conformance 2130/2130 in both. Version
  2026.11.16.10.
- 2026-11-16: AM/AM and AM/PM (ADR 0113): `am_am_pm(input, output, edges_db)` (C#
  `Measurements.AmAmPm`) bins paired complex samples by input level `20·log10|x|` and gives each
  bin's gain and phase from the mean complex ratio `y/x` (so a bin across the ±180° wrap
  averages correctly), with its centre level and count; empty bins are NaN. The vectors run the
  Saleh model on samples set to one amplitude per bin, by hand; the tests read a Rapp limiter's
  curve through `gain_compression` to its analytic 1 dB point. The C# conformance runner now
  compares integer arrays.
  Python 4224 passed, 2 skipped; .NET 3566 passed; conformance 2139/2139 in both. Version
  2026.11.16.11.
- 2026-11-16: Saleh and Rapp amplifier models (ADR 0114): `saleh_amplifier(samples, alpha_a,
  beta_a, alpha_phi, beta_phi)` and `rapp_amplifier(samples, gain, saturation, smoothness)` (C#
  `Channel.SalehAmplifier`, `Channel.RappAmplifier`) on the complex envelope,
  `y = (x/r)·A(r)·e^{jΦ(r)}`, zero to zero; Rapp switches to `A_sat/(1 + u^{−2p})^{1/(2p)}` above
  the knee so a huge drive reads `A_sat`. Vectors are the formulas by hand at chosen samples;
  the tests read the curves back through `am_am_pm`, find Rapp's analytic 1 dB point through
  `gain_compression`, and Saleh's output peak at `1/√β_a`.
  Python 4260 passed, 2 skipped; .NET 3600 passed; conformance 2157/2157 in both. Version
  2026.11.16.12.
- 2026-11-16: phase noise with spurs removed (ADR 0115): `phase_noise_ssb` and
  `integrated_phase_noise` take `spur_offsets` (C# `spurOffsets`), the spurs' offsets in Hz.
  On a copy of the Welch PSD, each side of each offset, in order, has the spur's group (the
  carrier group's width) replaced by a straight line in linear PSD between the bins just outside
  it; a side past the spectrum is skipped, an edge past it takes the other edge's value, and a
  spur whose group would touch the carrier group is `invalid_argument`. Vectors are Jacobi-Anger
  spectra plus spur tones, worked by hand; the tests take a -20 dBc spur off Wiener phase noise
  and get the integral without it back.
  Python 4287 passed, 2 skipped; .NET 3625 passed; conformance 2174/2174 in both. Version
  2026.11.16.13.
- 2026-11-16: phase noise spur finder (ADR 0116): `phase_noise_spurs(samples, sample_rate,
  f_lo, f_hi, *, threshold_db=10.0, ...)` (C# `Measurements.PhaseNoiseSpurs`) reports each bin in
  the offset band that is the peak of its group and whose group power stands `threshold_db` above
  the straight line between its edge bins, the line ADR 0115 would put there. Its offset is signed
  and its level is the power above the line, in dBc; `abs(offsets)` feeds `spur_offsets`. The
  band may not come within 2w + 1 bins of the carrier. Vectors are Jacobi-Anger spectra plus
  spur tones, by hand; the tests find a -20 dBc spur on Wiener phase noise, find none on the
  noise alone, and remove what they find.
  Python 4315 passed, 2 skipped; .NET 3651 passed; conformance 2186/2186 in both. Version
  2026.11.16.14.
- 2026-11-16: fifth-order intermodulation and IP5 (ADR 0117): `two_tone_ip5(samples,
  sample_rate, f1, f2, ...)` (C# `Measurements.TwoToneIp5`) claims DC, the tones, then
  `3f1 - 2f2` and `3f2 - 2f1` as `two_tone_ip2` does, and reports `ip5_db = 10 log10 P_t -
  worst_imd_dbc/4`. Vectors expand `x + a5 x^5` on two cosines and `x + a5 |x|^4 x` on two
  exponentials exactly, by hand, including a folded product; the tests check the expansion at two
  drives and the textbook limit `A_IP5^4 = 8/(5|a5|)`.
  Python 4334 passed, 2 skipped; .NET 3669 passed; conformance 2195/2195 in both. Version
  2026.11.16.15.
- 2026-11-16: noise power ratio (ADR 0118): `noise_power_ratio(frequencies, psd, band, notch, *,
  span=None)` (C# `Spectral.NoisePowerRatio`) is the mean PSD of the band outside the notch over
  the mean PSD in the notch, by the channel power rule, in dB; `+inf` for an empty notch. Vectors
  are short PSDs worked by hand; the tests fill a notched multitone's notch with a cubic and check
  the result against the cubic expanded by convolution, and the 2 dB-per-dB slope.
  Python 4353 passed, 2 skipped; .NET 3689 passed; conformance 2206/2206 in both. Version
  2026.11.16.16.
- 2026-11-16: power CCDF (ADR 0119): `power_ccdf(samples, levels_db)` (C#
  `Measurements.PowerCcdf`) is the fraction of samples whose `|x|²` is strictly above the mean
  power by each level; `power_ccdf_level(samples, probability)` (C# `Measurements.PowerCcdfLevel`)
  reads it the other way, the `(⌊pN⌋ + 1)`-th largest power over the mean in dB, the PAPR for
  `p < 1/N`. Vectors are integer-power sets counted by hand, with ties; the tests check complex
  Gaussian noise against `exp(−g)` and real Gaussian noise against `erfc(√(g/2))`.
  Python 4378 passed, 2 skipped; .NET 3714 passed; conformance 2222/2222 in both. Version
  2026.11.16.17.
- 2026-11-16: spectral flatness (ADR 0120): `spectral_flatness(frequencies, psd, *, band=None,
  span=None)` (C# `Spectral.SpectralFlatness`) is the geometric mean of the PSD over its arithmetic
  mean, each bin weighted by its overlap with the band, by the channel power rule's bins; 0 and
  `−∞` dB when a weighted bin is zero. Vectors are short PSDs worked by hand; the tests check the
  two-level closed form, a tone, white noise against `exp(−γ)`, and scale invariance.
  Python 4398 passed, 2 skipped; .NET 3734 passed; conformance 2235/2235 in both. Version
  2026.11.16.18.
- 2026-11-16: spectral centroid and RMS bandwidth (ADR 0121): `spectral_moments(frequencies, psd, *,
  band=None, span=None)` (C# `Spectral.SpectralMoments`) integrates the PSD as a step density
  over the band exactly: power, centroid, and the RMS spread about the centroid, so a flat band
  of width `B` gives `B/√12`. Vectors are worked in exact fractions from `E f²`; the tests check
  rectangles, a cut band, a Gaussian PSD, an axis shift and agreement with channel power.
  Python 4417 passed, 2 skipped; .NET 3753 passed; conformance 2247/2247 in both. Version
  2026.11.16.19.
- 2026-11-16: x dB bandwidth (ADR 0122): `db_bandwidth(frequencies, psd, drop_db, *, band=None)`
  (C# `Spectral.DbBandwidth`) walks out from the peak (the first on ties) to the first bin at or
  below `drop_db` under it on each side and interpolates the edge linearly in power; no crossing
  is an error. Vectors are short PSDs worked by hand with Fractions; the tests check a Gaussian
  PSD's `2σ·sqrt(x·ln 10 / 5)`, a rectangle, scaling, and a dip that ends the walk.
  Python 4435 passed, 2 skipped; .NET 3771 passed; conformance 2259/2259 in both. Version
  2026.11.16.20.
- 2026-11-16: single-tone frequency (ADR 0123): `kay_frequency(samples, sample_rate)` (C#
  `Measurements.KayFrequency`) is Kay's weighted phase-difference estimator, with the phase step
  as `atan2` of `x[n+1]·conj x[n]` written out, and parabolic weights that sum to 1. Zero samples
  are an error, because their phase depends on the zero's sign bits. The vectors use samples on
  the axes and noiseless tones. The tests sweep exact tones and check that the variance at 30 dB
  SNR is within 15 % of the CRLB.
  Python 4459 passed, 2 skipped; .NET 3797 passed; conformance 2272/2272 in both. Version
  2026.11.16.21.
- 2026-11-16: spectral rolloff (ADR 0124): `spectral_rolloff(frequencies, psd, fraction, *,
  band=None, span=None)` (C# `Spectral.SpectralRolloff`) walks the step density of the spectral
  moments to where the running power reaches `fraction` of the band's, interpolating linearly in
  that bin. Empty bins before the answer are passed over. Fraction 1 gives the top of the last
  bin with power. The vectors are worked by hand with Fractions, and the generator asserts that
  its walk agrees with each hand value. The tests cover a flat PSD, scaling, rising with the
  fraction, symmetry and a cut band.
  Python 4485 passed, 2 skipped; .NET 3823 passed; conformance 2287/2287 in both. Version
  2026.11.16.22.
- 2026-11-16: spectral crest factor (ADR 0125): `spectral_crest(frequencies, psd, *, band=None,
  span=None)` (C# `Spectral.SpectralCrest`) gives `SpectralCrest(peak, mean, crest, crest_db)`.
  The peak is over every bin that overlaps the band, and the mean is weighted by overlap, as for
  the flatness. The vectors are worked by hand with Fractions, including a bin that only touches
  the band. The tests cover scaling, a tone over an exponential noise floor, crest ≥ 1, and a
  flat PSD.
  Python 4499 passed, 2 skipped; .NET 3837 passed; conformance 2297/2297 in both. Version
  2026.11.16.23.
- 2026-11-16: spectral skewness and kurtosis (ADR 0126): `spectral_shape(frequencies, psd, *,
  band=None, span=None)` (C# `Spectral.SpectralShape`) integrates the step density of the
  spectral moments exactly about the centroid. The result is `SpectralShape(skewness, kurtosis)`,
  not excess, so a flat band gives 0 and 9/5. The vectors use Fraction raw moments expanded
  binomially, a different route from the libraries'. The tests cover mirroring, axis shift and
  stretch, scaling, a Gaussian with the step's own spread, and a flat cut band.
  Python 4515 passed, 2 skipped; .NET 3854 passed; conformance 2308/2308 in both. Version
  2026.11.16.24.
- 2026-11-16: spectral slope (ADR 0127): `spectral_slope(frequencies, psd, *, band=None,
  span=None, db=False)` (C# `Spectral.SpectralSlope`) is the continuous least-squares line
  through the PSD's step function over the band (in dB with `db`). It gives `SpectralSlope(center,
  level, slope)`, with the level at the band's centre. A line sampled into `M` bins gives
  `β(1 − 1/M²)`, the staircase effect, which is documented. With `db`, zero bins are an error.
  The vectors are Fraction solutions of the uncentered normal equations, with dB on powers of ten.
  The tests cover sampled lines, level × width = power, mirroring, axis shift, and an exponential
  PSD in dB.
  Python 4536 passed, 2 skipped; .NET 3875 passed; conformance 2320/2320 in both. Version
  2026.11.16.25.
- 2026-11-16: spectral entropy (ADR 0128): `spectral_entropy(frequencies, psd, *, band=None,
  span=None)` (C# `Spectral.SpectralEntropy`) is the differential entropy of the band's step
  density normalized to unit power. It gives `SpectralEntropy(entropy, entropy_bandwidth,
  normalized)`, with the bandwidth `exp(entropy)` in Hz and `normalized` that over the band's
  width. The bandwidth was chosen over `entropy / ln W` because the entropy depends on the axis
  units. The vectors assert hand bandwidths in Fractions and compute the rest as `ln power −
  Σ q ln d`. The tests cover scaling, axis stretch, a tone, and white noise against `exp(γ − 1)`.
  Python 4550 passed, 2 skipped; .NET 3889 passed; conformance 2330/2330 in both. Version
  2026.11.16.26.
- 2026-11-16: spectral flux (ADR 0129): `spectral_flux(frequencies, previous, current, *,
  band=None, span=None, normalize=True, rectify=True)` (C# `Spectral.SpectralFlux`) is the L2
  distance `sqrt(∫ Δ² df)` between two frames' step densities over a band. With `normalize`
  each frame is first scaled to unit band power, and with `rectify` only rises count. The
  vectors assert the squared flux as an exact Fraction. The tests cover symmetry without
  rectifying, rises and falls adding in squares, and level changes when normalized.
  Python 4567 passed, 2 skipped; .NET 3906 passed; conformance 2343/2343 in both. Version
  2026.11.16.27.
- 2026-11-16: spectral decrease (ADR 0130): `spectral_decrease(frequencies, psd, *,
  band=None, span=None)` (C# `Spectral.SpectralDecrease`) weighs each later piece's change in
  density from the band's first piece by its width times `δ/(m_k − m_0)`, over the later
  pieces' power. On uncut bins it is exactly the library form `Σ (P_k − P_0)/k / Σ P_k`, and a
  cut band has a defined meaning. The vectors are exact Fractions with hand values. The tests
  cover scaling, axis stretch and the library form.
  Python 4579 passed, 2 skipped; .NET 3918 passed; conformance 2352/2352 in both. Version
  2026.11.16.28.
- 2026-11-16: spectral variation (ADR 0131): `spectral_variation(frequencies, previous,
  current, *, band=None, span=None)` (C# `Spectral.SpectralVariation`) is `1 − ∫ d₀d₁ df /
  (‖d₀‖ ‖d₁‖)` on two frames' step densities over a band, in [0, 1]. The vectors assert the
  correlation squared as an exact Fraction. The tests cover swapping the frames, scaling, and
  the range on random frames.
  Python 4592 passed, 2 skipped; .NET 3931 passed; conformance 2362/2362 in both. Version
  2026.11.16.29.
- 2026-11-16: spectral irregularity (ADR 0132): `spectral_irregularity(frequencies, psd, *,
  band=None, span=None)` (C# `Spectral.SpectralIrregularity`) gives the squared jumps between
  neighbouring pieces of the step density, each weighted by the two pieces' mean width, over
  the squared norm. On uncut bins this is exactly Jensen's form, and a sliver at a band edge
  counts for little. The vectors are exact Fractions with hand values. The tests cover scaling,
  axis stretch, reversal and Jensen's form.
  Python 4606 passed, 2 skipped; .NET 3945 passed; conformance 2372/2372 in both. Version
  2026.11.16.30.
- 2026-11-16: spectral contrast (ADR 0133): `spectral_contrast(frequencies, psd, *,
  band=None, span=None, fraction=0.2)` (C# `Spectral.SpectralContrast`) sorts the band's pieces
  by density. `peak` is the mean over the top `fraction` of the band's width and `valley` the
  mean over the bottom; a straddling piece counts only for the width needed. It gives
  `SpectralContrast(peak, valley, contrast_db)`, with +∞ for a zero valley. The vectors assert
  the peak and valley exactly in Fractions. The tests cover scaling, the half split's mean, a
  zero valley, and a tone over a floor at 40 dB.
  Python 4622 passed, 2 skipped; .NET 3961 passed; conformance 2384/2384 in both. Version
  2026.11.16.31.
- 2026-11-16: band energy ratio (ADR 0134): `band_energy_ratio(frequencies, psd, split, *,
  band=None, span=None)` (C# `Spectral.BandEnergyRatio`) integrates the band's step density
  below and above `split`, sharing a straddling bin by width. It gives `BandEnergyRatio(low,
  high, ratio, ratio_db)`. The ratio is +∞ for zero `low`, and 0 (−∞ dB) for zero `high`. The
  vectors assert both powers exactly in Fractions. The tests check the sum against
  `channel_power`, mirroring, and both infinite cases.
  Python 4636 passed, 2 skipped; .NET 3975 passed; conformance 2394/2394 in both. Version
  2026.11.16.32.
- 2026-11-16: spectral peaks (ADR 0135): `spectral_peaks(frequencies, psd, *,
  min_prominence=0.0)` (C# `Spectral.SpectralPeaks`) lists each maximal run of equal values with
  both neighbours strictly lower, as `SpectralPeak(index, frequency, height, prominence)` in order
  of frequency. The edge bins are never peaks, a plateau's frequency is its middle, and each base
  stops at the first strictly higher bin. The vectors are worked by hand: nested peaks, odd and
  even plateaus, edges, a shoulder, equal neighbours, thresholds. The tests cover scaling, the
  threshold and two tones in noise. ADRs 0133 and 0134 no longer say ∞ can't be a vector; their
  zero-valley and zero-power cases are vectors now, written `"inf"` and `"-inf"`.
  Python 4661 passed, 2 skipped; .NET 4000 passed; conformance 2412/2412 in both. Version
  2026.11.16.33.
- 2026-11-16: peak interpolation (ADR 0136): `interpolate_peak(frequencies, psd, index, *,
  scale="db")` (C# `Spectral.InterpolatePeak` with `PeakScale`) fits a parabola through the peak
  bin and its neighbours, on the dB scale (exact for a Gaussian) or the linear one (exact for a
  parabola). It gives `PeakEstimate(frequency, height, offset)`, with `|offset| ≤ 1/2`; two equal
  top bins give their middle. The vectors are parabolas and Gaussians at known vertices, worked
  analytically. The tests cover Gaussians shifted across a bin, scaling, and a Hann-windowed
  tone between bins.
  Python 4685 passed, 2 skipped; .NET 4023 passed; conformance 2427/2427 in both. Version
  2026.11.16.34.
- 2026-11-16: find tones (ADR 0137): `find_tones(frequencies, psd, count, *,
  min_prominence=0.0, scale="db")` (C# `Spectral.FindTones`) ranks the `spectral_peaks` by
  prominence, highest first with ties to the lower frequency, and keeps `count`. It refines each
  with `interpolate_peak` into `Tone(index, frequency, height, prominence)`. A peak whose fit is
  undefined (a flat plateau, or a zero bin on the dB scale) keeps its grid values. The fit now
  lives in one helper that both functions use. The vectors are Gaussians sampled on three bins,
  so their vertices are known analytically, plus hand-worked plateaus, a zero neighbour and a
  tie. The tests compare against the two functions it composes, and find two Hann-windowed
  tones in noise.
  Python 4701 passed, 2 skipped; .NET 4038 passed; conformance 2439/2439 in both. Version
  2026.11.16.35.
- 2026-11-16: peak widths (ADR 0138): `peak_widths(frequencies, psd, *, rel_height=0.5,
  min_prominence=0.0)` (C# `Spectral.PeakWidths`) measures each `spectral_peaks` peak where the
  PSD crosses `height − rel_height·prominence`, interpolating linearly between bins. It gives
  `PeakWidth(index, level, left, right, width)`. The vectors are triangles, an asymmetric peak,
  nested peaks and a plateau, with crossings worked by hand in Fractions. The tests cover
  scaling and a zero-padded Hann lobe's half-power width of 1.44 bins.
  Python 4718 passed, 2 skipped; .NET 4055 passed; conformance 2451/2451 in both. Version
  2026.11.16.36.
- 2026-11-16: harmonic series (ADR 0139): `harmonic_series(frequencies, tolerance, *,
  max_order=10)` (C# `Spectral.HarmonicSeries`) tries every `t_i/m` as the fundamental and keeps
  the candidate matching the most tones within `tolerance` Hz, ties to the highest. It refines
  the winner by least squares over its matched tones. It gives `HarmonicSeries(fundamental,
  orders, matched)`, with order 0 for an unmatched tone. The vectors are worked by hand: exact
  and detuned harmonics, a stray tone at two `max_order`s, a missing fundamental. The tests cover
  permuting and scaling the tones, and a clipped sine through `find_tones`.
  Python 4731 passed, 2 skipped; .NET 4068 passed; conformance 2461/2461 in both. Version
  2026.11.16.37.
- 2026-11-16: inharmonicity (ADR 0140): `inharmonicity(frequencies, heights, fundamental,
  orders)` (C# `Spectral.Inharmonicity`) is `(2/f0)·Σ h|t − m·f0| / Σ h` over the tones with
  order at least 1. It takes `harmonic_series` output and `find_tones` heights. It is
  dimensionless: 0 for exact harmonics, 1 for partials half a fundamental away. The vectors are
  worked by hand in Fractions. The tests cover scaling the frequencies and the heights, and a
  stiff-string series that grows with stiffness.
  Python 4746 passed, 2 skipped; .NET 4083 passed; conformance 2473/2473 in both. Version
  2026.11.16.38.
- 2026-11-16: odd-to-even ratio (ADR 0141): `odd_even_ratio(heights, orders)` (C#
  `Spectral.OddEvenRatio`) is the power in odd harmonic orders, with the fundamental counted as
  odd, over the power in even ones. Order 0 is left out. No even power gives `+inf`, and no power
  at all is `invalid_argument`. The vectors are worked by hand in Fractions. The tests cover
  scaling and permuting, and a clipped sine through `find_tones` and `harmonic_series`, which is
  odd only.
  Python 4760 passed, 2 skipped; .NET 4097 passed; conformance 2484/2484 in both. Version
  2026.11.16.39.
- 2026-11-16: tristimulus (ADR 0142): `tristimulus(heights, orders)` (C# `Spectral.Tristimulus`)
  gives the shares of harmonic amplitude, `sqrt` of the power heights, in the fundamental, in
  orders 2–4 and in orders 5 and up. Order 0 is left out. The vectors use perfect-square heights,
  worked in Fractions. The tests cover scaling, the shares summing to 1, and a sawtooth's `1/m`
  amplitudes.
  Python 4772 passed, 2 skipped; .NET 4109 passed; conformance 2493/2493 in both. Version
  2026.11.16.40.
- 2026-11-16: harmonic-to-noise ratio (ADR 0143): `harmonic_to_noise(frequencies, psd,
  fundamental, half_width)` (C# `Spectral.HarmonicToNoise`) sorts whole bins. A bin within
  `half_width` Hz of some `m·f0`, `m ≥ 1`, is harmonic; every other bin, DC included, is noise.
  It gives `HarmonicToNoise(harmonic, noise, ratio, ratio_db)`, with infinities as for the band
  energy ratio. The vectors list the harmonic bins by hand and check them against the rule, with
  the sums worked in Fractions. The tests cover scaling the PSD, and a sine in white noise
  (ratio about 50) as a statistic.
  Python 4786 passed, 2 skipped; .NET 4123 passed; conformance 2505/2505 in both. Version
  2026.11.16.41.
- 2026-11-16: harmonic spectral deviation (ADR 0144): `harmonic_deviation(heights, orders)` (C#
  `Spectral.HarmonicDeviation`) is `Σ|a_m − e_m| / Σ a_m` over orders 1 to the highest. The
  amplitudes are `a_m = sqrt` of each order's summed power, 0 for a missing order, and the
  envelope `e_m` is the mean of the amplitude and its neighbours. The vectors use perfect-square
  powers, worked in Fractions and checked against the definition. The tests cover scaling, and a
  linear fall that deviates only at its two ends.
  Python 4800 passed, 2 skipped; .NET 4137 passed; conformance 2517/2517 in both. Version
  2026.11.16.42.
- 2026-11-16: harmonic centroid and spread (ADR 0145): `harmonic_centroid(frequencies, heights,
  orders)` (C# `Spectral.HarmonicCentroid`) is the mean of the matched tones' measured
  frequencies, weighted by amplitude `sqrt(height)`, with their weighted standard deviation
  about it. Both are in Hz, and order 0 is left out. The vectors use perfect-square heights,
  worked in Fractions and checked against the definition. The tests cover scaling the heights
  and the frequencies.
  Python 4813 passed, 2 skipped; .NET 4150 passed; conformance 2528/2528 in both. Version
  2026.11.16.43.
- 2026-11-16: zero-crossing rate (ADR 0146): `zero_crossing_rate(samples)` (C#
  `Measurements.ZeroCrossingRate`) is the share of adjacent sample pairs whose signs differ. A
  sample is positive when `x >= 0`, so 0 and -0.0 count as positive. Real samples only (Python
  rejects complex). Not framed. The vectors are counted by hand. The tests cover a sine (twice
  per cycle), positive scaling and complex input.
  Python 4827 passed, 2 skipped; .NET 4163 passed; conformance 2539/2539 in both. Version
  2026.11.16.44.
- 2026-11-16: temporal centroid (ADR 0147): `temporal_centroid(samples, sample_rate)` (C#
  `Measurements.TemporalCentroid`, real and complex) is the mean of the sample times `n / fs`,
  weighted by energy `|x|²`, with its weighted standard deviation. Both are in seconds, with
  sample 0 at t = 0. The vectors are worked in Fractions and checked against the definition.
  The tests cover a delay (only the centroid moves) and complex scaling.
  Python 4840 passed, 2 skipped; .NET 4176 passed; conformance 2550/2550 in both. Version
  2026.11.16.45.
- 2026-11-16: autocorrelation (ADR 0148): `autocorrelation(samples, max_lag=None, *,
  scaling="biased")` (C# `Dsp.Autocorrelation`, real and complex, with `CorrelationScaling`).
  It is `r[k] = Σ x[n+k]·conj x[n]` for lags 0 to `max_lag`, NumPy's `correlate` side. It is
  scaled by `1/N` (the default), `1/(N − k)` or not at all, and the mean is kept. The vectors are
  worked in exact (Gaussian) integers. The tests cover a direct two-sided sum (and the conjugate
  symmetry), the energy at lag 0, and a periodic signal peaking at its period.
  Python 4855 passed, 2 skipped; .NET 4191 passed; conformance 2562/2562 in both. Version
  2026.11.16.46.
- 2026-11-16: linear prediction by Levinson-Durbin (ADR 0149): `levinson(r, order)` (C#
  `Dsp.Levinson`, giving `Levinson` for real `r` and `ComplexLevinson` for complex `r`). It
  gives the prediction-error filter `a` (`a[0] = 1`, `e[n] = Σ a[j] x[n−j]`), the reflection
  coefficients and the final error. `r[0]` must be real and positive, and every `|k| < 1`. The
  vectors are checked by exact Gaussian elimination of each order's normal equations, over
  complex Fractions. The tests cover a dense Toeplitz solve, AR(2) recovery, and the error
  equal to the full residual's energy over `N`. The Python autocorrelation now computes lag 0
  from `re² + im²` so it is exactly real.
  Python 4872 passed, 2 skipped; .NET 4207 passed; conformance 2576/2576 in both. Version
  2026.11.16.47.
- 2026-11-16: autocorrelation pitch (ADR 0150): `autocorrelation_pitch(samples, sample_rate,
  min_frequency, max_frequency)` (C# `Measurements.AutocorrelationPitch`). It finds the highest
  biased autocorrelation peak among lags `ceil(fs/max)` to `floor(fs/min)` (ties go to the
  shorter lag). A parabola refines it only at a true local maximum. It returns
  `AutocorrelationPitch(frequency, lag, voicing = r[L]/r[0])`. The vectors are worked from the
  definition in Fractions, with hand values for the symmetric, edge and tie cases. The tests
  cover a period of 36.6 samples recovered to 0.5% and scaling.
  Python 4887 passed, 2 skipped; .NET 4221 passed; conformance 2588/2588 in both. Version
  2026.11.16.48.
- 2026-11-16: real cepstrum (ADR 0151): `real_cepstrum(samples, nfft=None)` (C#
  `Spectral.RealCepstrum`) is `Re IFFT(ln|FFT(x, nfft)|)`, with a natural log and all `nfft`
  values. A zero bin is `invalid_argument`. The vectors come from the series of
  `ln|1 + a e^(−jω)|`, aliased at `nfft` bins and summed in Fractions. They cover a
  minimum-phase pair, its time reverse, a delay, a negative `a` with odd `nfft`, a gain, the
  default `nfft` and an impulse. The tests cover a pulse train peaking at its period, evenness
  and complex rejection.
  Python 4901 passed, 2 skipped; .NET 4234 passed; conformance 2599/2599 in both. Version
  2026.11.16.49.
- 2026-11-16: cepstrum pitch (ADR 0152): `cepstrum_pitch(samples, sample_rate, min_frequency,
  max_frequency, nfft=None)` (C# `Measurements.CepstrumPitch`). It finds the highest real-cepstrum
  peak among the quefrencies `ceil(fs/max)` to `floor(fs/min)`, with `2·hi < nfft`. The peak and
  the parabola follow ADR 0150, through a private helper the two pitch functions now share. It
  returns `CepstrumPitch(frequency, quefrency, strength = c[L])`. The vectors come from the
  Fractions series of an echo `δ + a·δ[n−P]`, aliased at `nfft`. They cover an echo, an
  adjacent two-tap with a moved peak, a rising edge, an impulse tie, and the errors.
  Python 4915 passed, 2 skipped; .NET 4247 passed; conformance 2610/2610 in both. Version
  2026.11.16.50.
- 2026-11-16: minimum phase from the cepstrum (ADR 0153): `minimum_phase(samples, nfft=None)`
  (C# `Spectral.MinimumPhase`) folds the real cepstrum and returns `Re IFFT(exp(FFT(ĉ)))`, all
  `nfft` values. The fold keeps `c[0]` and the even-`M` middle, and doubles `1 … ⌈M/2⌉−1`. The
  default `nfft` is the smallest power of two `≥ max(64, 8N)`, because the cepstrum aliases.
  The vectors are analytic: zeros outside the circle reflect to `1/z` with gain `|z|`, multiplied
  out in Fractions, with the aliasing bound checked. The tests cover the magnitude being kept,
  the partial energies, and (in Python) the zeros lying inside.
  Python 4930 passed, 2 skipped; .NET 4260 passed; conformance 2621/2621 in both. Version
  2026.11.16.51.
- 2026-11-16: mel scale (ADR 0154): `hz_to_mel(hz, *, scale="htk")` and `mel_to_hz` in `units`
  (C# `Units.HzToMel`, `Units.MelToHz`, `MelScale { Htk, Slaney }`), elementwise in Python. HTK
  is `2595·log10(1 + f/700)`. Slaney is linear at 200/3 Hz per mel to 1 kHz, then 27 mel per
  factor of 6.4. Values are finite and `≥ 0`. The vectors are exact points (`6300 ↦ 2595`,
  `6400 ↦ 42` Slaney) and 50-digit `decimal` values, both ways. The tests cover the round trip,
  monotonicity, and arrays.
  Python 4962 passed, 2 skipped; .NET 4288 passed; conformance 2647/2647 in both. Version
  2026.11.16.52.
- 2026-11-16: mel filterbank (ADR 0155): `mel_filterbank(n_filters, nfft, sample_rate,
  min_frequency=0.0, max_frequency=None, *, scale="htk", area_normalized=False)` (C#
  `Spectral.MelFilterbank`, `double[][]`). It builds triangles on `n_filters + 2` edges equally
  spaced in mel, evaluated at the bin frequencies `k·fs/nfft`, with optional Slaney area
  normalization. All-zero rows are allowed. The vectors are worked in 50-digit `decimal`, with
  hand rows on the linear part of the Slaney scale (edges every 200 Hz). The tests cover
  adjacent filters summing to 1 and unit area.
  Python 4981 passed, 2 skipped; .NET 4306 passed; conformance 2662/2662 in both. Version
  2026.11.16.53.
- 2026-11-16: DCT-II (ADR 0156): `dct(samples, *, orthonormal=True)` and `idct(coefficients, *,
  orthonormal=True)` (C# `Spectral.Dct`, `Spectral.Idct`). Orthonormal by default, or `2Σ` as
  SciPy's default; `idct` is always the exact inverse. Computed directly from one cosine table
  indexed `k(2n+1) mod 4N`, so both languages use the same cosines. The vectors use exact
  cosines for `N = 1, 2, 4` in 50-digit `decimal`; the tests cover round trips, orthogonality and
  energy.
  Python 5020 passed, 2 skipped; .NET 4339 passed; conformance 2687/2687 in both. Version
  2026.11.16.54.
- 2026-11-16: MFCC (ADR 0157): `mfcc(power_spectrum, filterbank, n_coefficients, *,
  floor=1e-10)` (C# `Spectral.Mfcc`). It takes one frame and any filterbank: `ln(max(W @ P,
  floor))`, then the orthonormal `dct`, keeping the first `n_coefficients` with `c_0`. There is
  no liftering. The vectors use exact cosines for `N = 2, 3, 4` and logs in 50-digit
  `decimal`. The tests check that scaling the power moves only `c_0`, by `√N·ln a`.
  Python 5038 passed, 2 skipped; .NET 4357 passed; conformance 2703/2703 in both. Version
  2026.11.16.55.
- 2026-11-16: delta coefficients (ADR 0158): `delta(frames, width=2)` (C# `Spectral.Delta`,
  `double[][]`). It uses the HTK regression `Σ n (c_{t+n} − c_{t−n}) / (2 Σ n²)` per column,
  with indices clamped to the first and last frames, so the output has `T` rows. The vectors
  are exact fractions. A ragged-frames case is a unit test in both languages, not a vector,
  because the Python vector decoder can't build a ragged array.
  Python 5052 passed, 2 skipped; .NET 4371 passed; conformance 2712/2712 in both. Version
  2026.11.16.56.
- 2026-11-16: cepstral liftering (ADR 0159): `cepstral_lifter(coefficients, length=22)` (C#
  `Spectral.CepstralLifter`), the HTK sinusoidal lifter `(1 + (L/2)·sin(π n/L))·c_n` on one
  frame. `L ≥ 1`, with no inverse, since the weight can be 0 past `n = L`. The vectors use exact
  sines of 15° steps for `L = 12`, plus `L = 1`, `2` and the default 22.
  Python 5063 passed, 2 skipped; .NET 4381 passed; conformance 2721/2721 in both. Version
  2026.11.16.57.
- 2026-11-16: ERB scale (ADR 0160): `hz_to_erb_rate`, `erb_rate_to_hz` and `erb_bandwidth` in
  `units` (C# `Units.HzToErbRate`, `ErbRateToHz`, `ErbBandwidth`). They use the published
  Glasberg & Moore constants: `24.7·(4.37 f/1000 + 1)` and `21.4·log10(4.37 f/1000 + 1)`. A
  first draft of the ADR said the rounding was 0.14 %; the slope test showed `≈ 0.32 %`
  (`21.4·24.7·4.37/(1000 ln 10) ≈ 1.0032`), and the ADR was corrected before it was committed.
  Python 5087 passed, 2 skipped; .NET 4410 passed; conformance 2743/2743 in both. Version
  2026.11.16.58.
- 2026-11-16: gammatone (ADR 0161): `gammatone(center_frequency, sample_rate, length, *, order=4,
  bandwidth_factor=1.019)` in `dsp` (C# `Dsp.Gammatone`). It gives sampled taps `t^(N−1)·exp(−2π
  b ERB t)·cos(2π f_c t)`, scaled to exactly unit gain at `f_c`. A zero response, such as one
  tap of order ≥ 2, is an error. The vectors use the closed form in 60-digit `decimal`, with π
  from Machin's formula and Taylor cos and sin. The tests check the order-4 −3 dB width
  `2√(2^(1/4) − 1)·b·ERB` to 2 %.
  Python 5102 passed, 2 skipped; .NET 4424 passed; conformance 2756/2756 in both. Version
  2026.11.16.59.
- 2026-11-16: ERB-spaced frequencies (ADR 0162): `erb_space(min_frequency, max_frequency,
  n_frequencies)` in `units` (C# `Units.ErbSpace`). It gives equal ERB-rate steps, ascending,
  with the endpoints returned exactly. `n = 1` gives `[min]`. The vectors are in 50-digit
  `decimal`, with a point placed at `E = 21.4` by construction.
  Python 5113 passed, 2 skipped; .NET 4435 passed; conformance 2766/2766 in both. Version
  2026.11.16.60.
- 2026-11-16: Bark scale (ADR 0163): `hz_to_bark` and `bark_to_hz` in `units` (C#
  `Units.HzToBark`, `Units.BarkToHz`), after Traunmüller (1990) with both end corrections always
  applied. The inverse is closed form by branch and clamped at 0. Its domain runs from
  `hz_to_bark(0)` to the limit 27.6396. The vectors are exact in `fractions`, with points on
  both sides of each branch edge.
  Python 5138 passed, 2 skipped; .NET 4460 passed; conformance 2788/2788 in both. Version
  2026.11.16.61.
- 2026-11-16: frequency weightings (ADR 0164): `a_weighting` and `c_weighting` in `units` (C#
  `Units.AWeighting`, `Units.CWeighting`), the IEC 61672-1 curves in dB from the four pole
  frequencies. Each is normalized by its own computed value at 1 kHz, so it is exactly 0 there.
  The result is `−inf` at 0 Hz. The code works in logs with `hypot`, so large frequencies do
  not overflow. The vectors are in 50-digit `decimal`. The generator asserts the standard's
  rounded `A1000 = −2.000` and `C1000 = −0.062`, and its 0.1 dB nominal table at 14 base-10
  frequencies.
  Python 5163 passed, 2 skipped; .NET 4487 passed; conformance 2810/2810 in both. Version
  2026.11.16.62.
- 2026-11-16: weighting filters (ADR 0165): `a_weighting_sos(sample_rate)` and
  `c_weighting_sos(sample_rate)` in `dsp` (C# `Dsp.AWeightingSos`, `Dsp.CWeightingSos`). Each
  section is the product of two bilinear-transformed first-order factors, without prewarping.
  The first section is scaled so the gain at 1 kHz is exactly 1, from the analog magnitude at
  `2fs·tan(π·1000/fs)`. `fs > 2000`. The vectors are in 60-digit `decimal`. The tests check
  the exact bilinear identity: the response in dB at `f` equals the ADR 0164 curve at
  `(fs/π)·tan(πf/fs)`, relative to 1 kHz, to 1e-9.
  Python 5185 passed, 2 skipped; .NET 4509 passed; conformance 2826/2826 in both. Version
  2026.11.16.63.
- 2026-11-16: time weighting (ADR 0166): `time_weighting(samples, sample_rate, time_constant)`
  in `measurements` (C# `Measurements.TimeWeighting`, real and complex). It is the exponential
  average `y[n] = α y[n−1] + (1 − α)|x[n]|²`, with `α = exp(−1/(τ fs))` and `1 − α` from
  `expm1`. It starts from 0 and gives one power per sample; the caller takes dB. `L_eq` is the
  existing `power_stats(...).mean_power`. The vectors come from the closed-form sum in 50-digit
  `decimal`, including a unit step at `τ·fs = 1`, which gives `1 − e^(−(n+1))`. The C#
  `Measurements` class is now `partial`.
  Python 5199 passed, 2 skipped; .NET 4523 passed; conformance 2838/2838 in both. Version
  2026.11.16.64.
- 2026-11-16: fractional-octave bands (ADR 0167): `octave_bands(fraction, min_frequency,
  max_frequency)` in `units` (C# `Units.OctaveBands`). It gives the IEC 61260-1 base-10 exact
  mid-band frequencies, for odd and even `b`, as rows `[lower, center, upper]`, for every band
  whose center lies in the range. An empty range gives 0 rows. The vectors use powers of
  `10^(3/10)` in 50-digit `decimal`. The generator asserts that the octave and third-octave
  centers lie within 1.5 % of the standard's nominal names.
  Python 5211 passed, 2 skipped; .NET 4535 passed; conformance 2848/2848 in both. Version
  2026.11.16.65.
- 2026-11-16: octave-band levels (ADR 0168): `octave_band_levels(samples, sample_rate, fraction,
  min_frequency, max_frequency, *, order=3)` in `measurements` (C# `Measurements.OctaveBandLevels`,
  real and complex). It gives one mean power per band of `octave_bands`. Each band runs
  `butterworth_bandpass(order, lower, upper, fs)` from rest over the whole input, transient
  included. A band whose upper edge reaches Nyquist is `invalid_argument`. The vectors come from
  an independent float design (the analog band poles through the bilinear transform), run as a
  plain-Python direct-form-I cascade, at relative `1e-9`. The tests check a tone at a band center
  and the white-noise power sum.
  Python 5224 passed, 2 skipped; .NET 4547 passed; conformance 2859/2859 in both. Version
  2026.11.16.66.
- 2026-11-16: exceedance levels (ADR 0169): `exceedance_levels(powers, percents)` in
  `measurements` (C# `Measurements.ExceedanceLevels`). `L_N` is the `1 − N/100` quantile of the
  powers by linear interpolation between order statistics (Hyndman–Fan type 7, NumPy's default),
  in power. `L_0` is the maximum and `L_100` the minimum. The vectors are hand-sorted series in
  exact fractions. A Python test checks the result against `np.quantile`.
  Python 5240 passed, 2 skipped; .NET 4562 passed; conformance 2873/2873 in both. Version
  2026.11.16.67.
- 2026-11-16: short Leq series and sound exposure (ADR 0170): `block_leq(samples, sample_rate,
  duration)` and `sound_exposure(samples, sample_rate)` in `measurements` (C#
  `Measurements.BlockLeq`, `Measurements.SoundExposure`, real and complex). `block_leq` gives
  the mean `|x|²` over blocks of `⌊duration·fs + 1/2⌋` samples, dropping a partial last block.
  `sound_exposure` gives `Σ|x|²/fs`. The vectors are exact hand sums in fractions.
  Python 5259 passed, 2 skipped; .NET 4580 passed; conformance 2890/2890 in both. Version
  2026.11.16.68.
- 2026-11-16: reverberation time (ADR 0171): `schroeder_decay(impulse_response)` and
  `reverberation_time(impulse_response, sample_rate, *, start_db=-5.0, stop_db=-25.0)` in
  `measurements` (C# `Measurements.SchroederDecay`, `Measurements.ReverberationTime`, real and
  complex). The first is the backward-integrated decay in dB. The second fits an ordinary
  least-squares line to the samples between the first crossings of the two levels and returns
  `T = −60/m`. A decay that never reaches `stop_db` is `invalid_argument`. The vectors come from
  the exact geometric tails of `r^n` decays, and their cross terms for two slopes, in 50-digit
  `decimal`. Long decays are checked against `60/(−20 log10 r·fs)`.
  Python 5278 passed, 2 skipped; .NET 4598 passed; conformance 2907/2907 in both. Version
  2026.11.16.69.
- 2026-11-16: clarity and definition (ADR 0172): `clarity(impulse_response, sample_rate, *,
  time=0.08)` and `definition(impulse_response, sample_rate, *, time=0.05)` in `measurements`
  (C# `Measurements.Clarity`, `Measurements.Definition`, real and complex). The response starts
  at index 0. The boundary is `N = ⌊time·fs + 1/2⌋`, and sample `N` counts as late. With no late
  energy, clarity is `+inf`; with no early energy, `−inf`. The vectors are exact hand sums and
  the geometric sums of `r^n` decays in 50-digit `decimal`.
  Python 5298 passed, 2 skipped; .NET 4617 passed; conformance 2925/2925 in both. Version
  2026.11.16.70.
- 2026-11-16: centre time (ADR 0173): `centre_time(impulse_response, sample_rate)` in
  `measurements` (C# `Measurements.CentreTime`, real and complex). It is the energy centroid
  `Σ (n/fs)|h|²/Σ|h|²` from index 0. The early decay time needs no new function: it is
  `reverberation_time(h, fs, start_db=0, stop_db=-10)`, and the tests pin it to
  `60/(−20 log10 r·fs)`. The vectors are exact hand sums, plus the closed-form geometric moments
  in 50-digit `decimal`, checked against the direct sums.
  Python 5311 passed, 2 skipped; .NET 4630 passed; conformance 2936/2936 in both. Version
  2026.11.16.71.
- 2026-11-16: interaural cross-correlation (ADR 0174): `iacc(left, right, sample_rate, *,
  max_lag=0.001)` in `measurements` (C# `Measurements.Iacc`). It is
  `max |Σ l[n]r[n+τ]|/√(E_l E_r)` over integer lags `|τ| ≤ ⌊max_lag·fs + 1/2⌋`, clipped to the
  length, over the whole real responses, and returns the value only. The windowed forms
  (`IACC_E`, `IACC_L`) are the caller's slices. The vectors are exact hand sums in fractions:
  - delayed and inverted copies give 1;
  - impulses that don't overlap give 0;
  - one case tests the rounding of the lag range.

  Python 5328 passed, 2 skipped; .NET 4646 passed; conformance 2951/2951 in both. Version
  2026.11.16.72.
- 2026-11-16: lateral energy fraction (ADR 0175): `lateral_fraction(omni, figure_eight,
  sample_rate, *, start=0.005, stop=0.08)` in `measurements` (C# `Measurements.LateralFraction`).
  - The formula is `Σ_{N_a ≤ n < N_b} h_8² / Σ_{n < N_b} h_o²`, with `N = ⌊t·fs + 1/2⌋`.
  - Both sums are clipped to the length.
  - The result is not clamped, so it can exceed 1.

  The vectors are exact hand sums and geometric window sums in 50-digit `decimal`.
  Python 5345 passed, 2 skipped; .NET 4663 passed; conformance 2966/2966 in both. Version
  2026.11.16.73.
- 2026-11-16: modulation transfer function (ADR 0176): `modulation_transfer(impulse_response,
  sample_rate, frequencies)` in `measurements` (C# `Measurements.ModulationTransfer`, real and
  complex). It is Schroeder's `|Σ |h|² e^{−j2πF n/fs}|/Σ |h|²` from index 0, one value per
  frequency. The vectors use the geometric closed form evaluated with `cmath`, plus exact hand
  pairs. A test checks `1/√(1 + (2πF T/(6 ln 10))²)` at 0.1 %. The textbook 13.8 is 6 ln 10
  rounded, and that rounding alone gave a 0.1 % miss.
  Python 5359 passed, 2 skipped; .NET 4677 passed; conformance 2979/2979 in both. Version
  2026.11.16.74.
- 2026-11-16: speech transmission index (ADR 0177): `speech_transmission_index(mtf)` in
  `measurements` (C# `Measurements.SpeechTransmissionIndex`). The input is a 7-band MTF matrix of
  any column count (14 for the full method, 2 for STIPA).
  - Each `m` becomes `SNR = 10 log10(m/(1 − m))`, clipped to ±15 dB, then `TI = (SNR + 15)/30`.
  - The TIs are averaged over each band.
  - The bands are combined with the IEC 60268-16:2020 male weights. The weights were checked
    against two independent published restatements of that edition.

  No level, masking or threshold corrections are applied. `Σα − Σβ = 1`, so a uniform MTF gives
  its TI. The vectors are worked in 50-digit `decimal`. The Python vector loader can't decode a
  ragged matrix, so the unequal-rows case is a unit test in both languages.
  Python 5374 passed, 2 skipped; .NET 4691 passed; conformance 2991/2991 in both. Version
  2026.11.16.75.
- 2026-11-16: sound strength (ADR 0178): `sound_strength(impulse_response, reference)` in
  `measurements` (C# `Measurements.SoundStrength`, real and complex). It is
  `G = 10 log10(Σ|h|²/Σ|h_ref|²)` against the free-field response at 10 m.
  - It takes no sample rate, and the two lengths may differ.
  - G80 and G_late are the caller's slices.
  - A silent response gives `−inf`, and a silent reference is invalid.

  The vectors are exact hand sums.
  Python 5386 passed, 2 skipped; .NET 4704 passed; conformance 3002/3002 in both. Version
  2026.11.16.76.
- 2026-11-16: stage support (ADR 0179): `stage_support(impulse_response, sample_rate, *,
  late=False)` in `measurements` (C# `Measurements.StageSupport`, real and complex). It is ISO
  3382-1 Annex C, `ST_early` and `ST_late` against the direct 0–10 ms.
  - The windows are half-open, with bounds `⌊t·fs + 1/2⌋`, clipped to the length.
  - A silent window gives `−inf`.
  - A silent direct window, or `fs < 50`, is invalid.

  The vectors are hand sums at 100 Hz and geometric window sums at 1 kHz.
  Python 5398 passed, 2 skipped; .NET 4716 passed; conformance 3013/3013 in both. Version
  2026.11.16.77.
- 2026-11-16: bass and treble ratio (ADR 0180): `bass_ratio(times)` and `treble_ratio(times)` in
  `measurements` (C# `Measurements.BassRatio`, `Measurements.TrebleRatio`).
  - Each takes six octave-band reverberation times, 125 Hz to 4 kHz, all finite and positive.
  - `BR = (T125 + T250)/(T500 + T1000)` and `TR = (T2000 + T4000)/(T500 + T1000)`.

  The vectors are exact fractions.
  Python 5418 passed, 2 skipped; .NET 4735 passed; conformance 3031/3031 in both. Version
  2026.11.16.78.
- 2026-11-16: early decay time (ADR 0181): `early_decay_time(impulse_response, sample_rate)` in
  `measurements` (C# `Measurements.EarlyDecayTime`, real and complex). It is exactly
  `reverberation_time` with `start_db=0, stop_db=-10`.

  The vectors use the exact geometric Schroeder tails, including a two-slope decay.
  Python 5429 passed, 2 skipped; .NET 4746 passed; conformance 3041/3041 in both. Version
  2026.11.16.79.
- 2026-11-16: decay curvature (ADR 0182): `decay_curvature(impulse_response, sample_rate)` in
  `measurements` (C# `Measurements.DecayCurvature`, real and complex). It is ISO 3382-2 Annex B,
  `C = 100·(T30/T20 − 1)` percent, from two `reverberation_time` fits with the same errors.

  The vectors use the exact geometric tails: about 0 for a single exponential, and positive for
  two slopes.
  Python 5437 passed, 2 skipped; .NET 4754 passed; conformance 3048/3048 in both. Version
  2026.11.16.80.
- 2026-11-16: noise-compensated decay (ADR 0183): `noise_compensated_decay(impulse_response, *,
  tail=0.1)` in `measurements` (C# `Measurements.NoiseCompensatedDecay`, real and complex). It
  is ISO 3382-1 §5.3.3 b.
  - The noise power `ν` is the mean `|h|²` of the last `⌊tail·N + 1/2⌋` samples.
  - `E[n] = Σ (|h|² − ν)` runs up to the noise window, so the result has `N − M` values.
  - `E ≤ 0` gives `−inf`.

  The vectors are exact rational sums of the stored samples.
  Python 5450 passed, 2 skipped; .NET 4766 passed; conformance 3059/3059 in both. Version
  2026.11.16.81.
- 2026-11-16: decay time from a curve (ADR 0184): `decay_time(decay, sample_rate, *, start_db=-5,
  stop_db=-25)` in `measurements` (C# `Measurements.DecayTime`). It is the ADR 0171 fit on a
  supplied dB curve, such as a noise-compensated decay.
  - `−inf` is allowed in the curve; NaN and `+inf` are not.
  - Python's `reverberation_time` now goes through it.

  The vectors are exact least-squares slopes in fractions.
  Python 5467 passed, 2 skipped; .NET 4782 passed; conformance 3074/3074 in both. Version
  2026.11.16.82.
- 2026-11-16: analytic signal (ADR 0185): `analytic_signal(samples)` in `spectral` (C#
  `Spectral.AnalyticSignal`, in a new `AnalyticSignal.cs`; `Spectral` is now partial).
  - It computes `ifft(fft(x)·W)` with Marple's weights: 1 at DC and at `N/2`, 2 for the positive
    bins and 0 for the negative bins.
  - The input must be real; complex input is invalid.

  The vectors are the closed forms `cos → e^{jθ}` and `sin → −j e^{jθ}` at bin frequencies, plus
  hand DFT sums of impulses.
  Python 5484 passed, 2 skipped; .NET 4793 passed; conformance 3084/3084 in both. Version
  2026.11.16.83.
- 2026-11-16: energy-time curve (ADR 0186): `energy_time_curve(impulse_response)` in
  `measurements` (C# `Measurements.EnergyTimeCurve`, in a new `EnergyTimeCurve.cs`).
  - It is `10·log10(|z|²/max|z|²)`, where `z` is the analytic signal.
  - The peak is 0 dB, and a zero envelope gives `−inf`.

  The vectors are hand impulse sums, an AM tone at bin frequencies and a constant.
  Python 5494 passed, 2 skipped; .NET 4802 passed; conformance 3092/3092 in both. Version
  2026.11.16.84.
- 2026-11-16: instantaneous frequency (ADR 0187): `instantaneous_frequency(samples,
  sample_rate)` in `spectral` (C# `Spectral.InstantaneousFrequency`).
  - It computes `fs/(2π)·arg(z[n+1]·conj z[n])` from the analytic signal.
  - It returns `N − 1` values in Hz, with no unwrapping.

  The vectors are closed-form analytic signals at bin frequencies: single tones, DC plus a tone,
  and two tones.
  Python 5506 passed, 2 skipped; .NET 4813 passed; conformance 3102/3102 in both. Version
  2026.11.16.85.
- 2026-11-16: Teager-Kaiser energy (ADR 0188): `teager_energy(samples)` in `measurements` (C#
  `Measurements.TeagerEnergy`, in a new `TeagerEnergy.cs`).
  - It computes `|x[n]|² − Re(x[n−1]·conj x[n+1])`.
  - It returns `N − 2` values, with no padding.
  - It takes real and complex input.

  The vectors come from trigonometric identities and hand sums.
  Python 5516 passed, 2 skipped; .NET 4823 passed; conformance 3111/3111 in both. Version
  2026.11.16.86.
- 2026-11-16: energy separation (ADR 0189): `energy_separation(samples, sample_rate)` in
  `measurements` (C# `Measurements.EnergySeparation`, with the `EnergySeparation` record).
  - It is DESA-2 on the Teager energies of `x` and of `x[n+1] − x[n−1]`.
  - The arccos argument is clamped to `[−1, 1]`, so frequencies lie in `[0, fs/4]`.
  - Where an energy is not positive, both values are NaN.

  The vectors come from the cosine identity and five-sample hand sums.
  Python 5528 passed, 2 skipped; .NET 4834 passed; conformance 3121/3121 in both. Version
  2026.11.16.87.
- 2026-11-16: cross-correlation (ADR 0190): `cross_correlation(x, y)` in `dsp` (C#
  `Dsp.CrossCorrelation`, in a new `CrossCorrelation.cs`).
  - It computes `r[k] = Σ x[n+k]·conj y[n]` for `k = −(M−1) … N−1`, with lag 0 at index `M − 1`.
  - It is unscaled, and matches NumPy's `correlate(x, y, "full")`.

  The vectors are hand sums, each checked against a direct loop.
  Python 5539 passed, 2 skipped; .NET 4844 passed; conformance 3130/3130 in both. Version
  2026.11.16.88.
- 2026-11-16: GCC-PHAT delay (ADR 0191): `gcc_phat(x, y, sample_rate, *, max_delay=None)` in
  `measurements` (C# `Measurements.GccPhat`, in a new `GccPhat.cs`), returning `GccPhat(delay,
  lag, peak)`.
  - Both inputs are zero-padded to `N + M − 1`, so the correlation does not wrap.
  - The weighting is `W = G/|G|`, with 0 where `G = 0`.
  - The lag sign matches `cross_correlation`.
  - A tie goes to the smallest lag. The parabolic refinement is used only inside the searched
    range.

  The vectors are delayed impulses, which give an exact unit peak, plus a zero-bin tie.
  Python 5555 passed, 2 skipped; .NET 4858 passed; conformance 3143/3143 in both. Version
  2026.11.16.89.
- 2026-11-16: magnitude-squared coherence (ADR 0192): `coherence(x, y, sample_rate, ...)` in
  `spectral` (C# `Spectral.Coherence`, in a new `Coherence.cs`), returning `Coherence(frequencies,
  values, num_segments)`.
  - It uses the `welch_psd` segments and arguments: `min(1, |Σ X·conj Y|²/(Σ|X|²·Σ|Y|²))` on
    one-sided bins.
  - It is NaN where an auto-spectrum is 0.
  - The Welch segment helper now also returns each segment's complex spectrum, in both languages.

  The vectors are hand-worked short segments, each checked against a direct DFT.
  Python 5567 passed, 2 skipped; .NET 4869 passed; conformance 3153/3153 in both. Version
  2026.11.16.90.
- 2026-11-16: transfer-function estimate H1 (ADR 0193): `transfer_function(x, y, sample_rate,
  ...)` in `spectral` (C# `Spectral.TransferFunction`), returning `TransferFunction(frequencies,
  response, num_segments)`.
  - It computes `H = Σ conj X·Y / Σ|X|²` over the `coherence` segments, giving a complex NaN
    where the input has no power.
  - `coherence` and `transfer_function` now share one cross-segment helper in each language.

  The vectors are hand DFTs, each checked against a direct DFT.
  Python 5576 passed, 2 skipped; .NET 4878 passed; conformance 3161/3161 in both. Version
  2026.11.16.91.
- 2026-11-16: cross-spectral density (ADR 0194): `cross_spectral_density(x, y, sample_rate, ...)`
  in `spectral` (C# `Spectral.CrossSpectralDensity`), returning `CrossSpectralDensity(frequencies,
  csd, num_segments)`.
  - It computes `Pxy = d·Σ conj X·Y/(K·fs·Σw²)` over the `coherence` segments, with the
    `welch_psd` doubling.
  - For `y = x` it is `welch_psd`, and `Pxy/Pxx` is H1.
  - Real input only.

  The vectors are hand DFTs, each checked against a direct DFT.
  Python 5585 passed, 2 skipped; .NET 4886 passed; conformance 3168/3168 in both. Version
  2026.11.16.92.
- 2026-11-16: transfer-function estimate H2 (ADR 0195): `transfer_function_h2(x, y, sample_rate,
  ...)` in `spectral` (C# `Spectral.TransferFunctionH2`), returning the `TransferFunction`
  result.
  - It computes `H2 = Σ|Y|²/Σ conj Y·X` over the H1 segments, giving a complex NaN where the
    cross-spectrum is 0.
  - `H1/H2` is the coherence, and a unit test checks this.

  The vectors include a case where segments disagree: H1 = 1/3 and H2 = 3.
  Python 5594 passed, 2 skipped; .NET 4895 passed; conformance 3176/3176 in both. Version
  2026.11.16.93.
- 2026-11-16: two-sided cross-spectral density for complex input (ADR 0196).
  - `cross_spectral_density` takes `one_sided`, as `welch_psd` does. Complex `x` or `y` (or
    `one_sided=False`) gives the undoubled `Σ conj X·Y/(K·fs·Σw²)` over all bins, in
    `fftshift` order.
  - C# has a `Complex` overload, and the real overload gains `oneSided`.
  - For `y = x` complex, the result equals the complex `welch_psd`.

  There are 4 new hand-DFT vectors and 1 error vector.
  Python 5601 passed, 2 skipped; .NET 4901 passed; conformance 3181/3181 in both. Version
  2026.11.16.94.
- 2026-11-16: complex input for coherence, H1 and H2 (ADR 0197).
  - Complex `x` or `y` gives all `M` bins in `fftshift` order, with the rules unchanged.
  - C# has `Complex` overloads.
  - The four cross-spectral functions now share one helper per language, and it handles both
    bin layouts.

  The new suite `complex_cross_spectra` has hand DFTs of length-2 complex segments.
  Python 5615 passed, 2 skipped; .NET 4914 passed; conformance 3193/3193 in both. Version
  2026.11.16.95.
- 2026-11-16: coherent output power (ADR 0198): `coherent_output_power(x, y, sample_rate,
  ...)` in `spectral` (C# `Spectral.CoherentOutputPower`, with real and complex overloads).
  - It splits `welch_psd(y)` into `γ²·Pyy` and the rest, which sum exactly to `Pyy`.
  - There are no NaN bins: `γ²` is taken as 0 where an auto-spectrum is 0.
  - A unit test recovers the noise PSD.

  Python 5625 passed, 2 skipped; .NET 4924 passed; conformance 3202/3202 in both. Version
  2026.11.16.96.

## Not built

Everything else in the brief: IIR designs beyond Butterworth, Chebyshev I/II, elliptic, Bessel and all-pass sections (all-pass design to a delay target), FIR design beyond windowed sinc, equiripple, least squares and frequency sampling, spectral estimators beyond Welch, the spectrogram
and Lomb-Scargle (multiband form), the rest of modulation (PSK/QAM
beyond QPSK, 8-PSK, 16-QAM and 64-QAM, FSK beyond 2- and 4-FSK in the link with noncoherent detection and fixed timing (FSK timing tracking, coherent detection, other modulation indices), OFDM beyond the link's prefix timing, preamble estimate, common-phase and window-offset tracking (pilots, time-varying channels), analog), impairments beyond AWGN, frequency offset, IQ imbalance, DC offset, Wiener phase noise and static multipath, fractional delay, block fading, a constant clock offset, linear clock drift and white clock jitter, tracking loops for modulations beyond QPSK, 8-PSK, 16-QAM and 64-QAM, equalizers beyond normalized LMS, its decision-feedback form, the least-squares start, the phase loop with its pilot slip correction, the constant-modulus (blind) form and RLS with its feedback form in the link (RLS for the blind form), decision-directed equalization beyond the link's preamble-trained ones, RF measurements (IMD beyond second, third and fifth order, ACPR channel filters beyond RRC,
NF beyond the Y-factor method and Friis' cascade), standards waveforms, file formats beyond SigMF, WAV and 1-D and 2-D `.npy` (`.npy` and `.npz` shapes beyond 2-D, streaming reads and writes,
per-channel SigMF metadata, WAV metadata beyond `LIST`/`INFO` tags and `cue ` points with `labl` labels and `ltxt` lengths), plotting, CLI,
packaging and publishing.

## Lessons

- 2026-11-16: NumPy's complex product `x * conj(x)` need not have an exactly zero imaginary part (it can
  use fused multiply-add), so a quantity defined as real, such as an autocorrelation's lag 0,
  is computed from `re² + im²` directly.
- 2026-11-13: Before putting a feature in Next, grep for it: "mixing" was planned while
  `frequency_offset` already multiplied by `e^(j(2π f n/fs + φ))` in both languages.
- 2026-11-12: The test for any dependency is whether it could ever force our code under the GPL or
  limit commercial shipping. A GPL label on a compiler runtime with the GCC exception does not.
- 2026-11-12: Check build tools' licenses too: hatchling and mypy both pull in pathspec (MPL-2.0).
  flit_core is clean. Whether a tool is shipped decides which licenses it may use (ADR 0005).
- 2026-11-12: NumPy's type stubs differ by version: Python 3.10 gets NumPy 2.2, which rejects a bare
  `np.ndarray` under strict mypy. Annotate with `NDArray[dtype]` and run mypy on both Pythons.
- 2026-11-12: Binary wheels can bundle libraries under other licenses; read the wheel's own
  `LICENSE.txt`, not just the project's top-level license.
- 2026-11-12: The `dotnet new xunit` template is xunit v2; there is no `xunit3` template in the SDK.
- 2026-11-16: `np.convolve(..., "same")` returns the longer input's length, so it pads a short
  signal out to the kernel. Pad explicitly when the data can be shorter than the kernel.
- 2026-11-12: Avoid long bash heredocs with quotes in JSON or C#; write such files directly.
- 2026-11-13: Windows PowerShell 5.1 splits a splatted `-m:1` into `- m : 1` for native commands;
  pass MSBuild switches as `/m:1`. Git Bash does the opposite: it turns `/m:1` into a path, so
  type `-m:1` there.
- 2026-11-13: Git Bash mangles backslash paths passed through `cmd /c`; run cmd invocations from
  the PowerShell tool instead.
- 2026-11-13: A conformance runner needs its own tests. Hand-written wrong cases
  (`vectors/selftest`) caught a C# runner that passed cases it never really ran.
- 2026-11-13: NumPy wheels bundle different native libraries per platform (Linux ships
  libquadmath, Windows doesn't). Check the wheels for every platform CI or users install, not
  only the local one.
- 2026-11-13: For a special function, check relative error over the whole range against the C
  library before trusting it. The naive `exp(-x*x)` in erfc costs about 1e-13 near x = 25 from
  the rounding of x²; splitting x into a short `z` plus a remainder fixes it. Below about 1e-308
  results are subnormal and relative error stops meaning anything.
- 2026-11-13: Test an estimator inside the whole chain, at the SNR it will be used at, before
  trusting it. The fourth-power frequency estimate looked fine at 20 dB and on clean vectors, but
  at 6 dB its error (0.1 to 0.5 Hz at Rs = 1000) turned a long frame by whole turns. A link test
  that skips a step when its parameter is zero (no frequency correction at 0 Hz) hides exactly this.
- 2026-11-13: Diff the two languages' full results, not just each against a partial expected
  value. A vector checks only the fields it lists, so a field one runner never sees (a Python
  property, where C# reflection sees every property) passes everywhere until the results are
  compared with each other.
- 2026-11-13: `np.asarray` returns the caller's own array when it already has the right dtype,
  so an object that keeps an argument (filter taps) must copy it with `np.array`. C# copies
  with `ToArray()` by habit; Python needs the same care, and a test that mutates the input.
- 2026-11-13: Size a Monte Carlo test from its expected error count, not by trying seeds: a
  window of ±k% needs about `(300/k)²` errors to sit at 3σ (500 for ±15 %). The FSK tests first
  had about 200 errors and ±12 %, passed in Python and failed in C# with unbiased code; ten
  seeds showed no bias, and resizing fixed it.
- 2026-11-13: A statistic over many symbols is only as tight as its least-averaged part. An
  OFDM run's channel estimate comes from `P` preamble blocks and is shared by every data block,
  so its error does not average out over the data: a binomial or per-symbol sd understates the
  spread of the BER and EVM when `P` is small. Make `P` large enough that the estimate's share is
  small (64 blocks here), or count runs, not symbols.
- 2026-11-13: Averaging estimates over time assumes nothing moved in between. A residual
  frequency error or phase noise turns each preamble block a little, and the plain mean of the
  blocks' channel estimates then starts with a phase off by the average turn, enough to lock a
  decision-directed loop a quadrant off. Align each block to a reference (or track through the
  preamble) before averaging.
- 2026-11-13: When a new stage makes the old metrics look broken, find where in the frame the
  errors are before tuning it. The equalized link's errors did not move with preamble length,
  because every one of them was in the preamble, made while the taps were still converging; and
  the one run that failed outright had the wrong frame start, from a coarse frequency error that a
  long preamble turned through a cycle, not from the equalizer at all.
