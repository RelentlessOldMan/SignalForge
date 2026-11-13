> **Note.** This is the original ChatGPT-drafted brief that started the project. It is the idea and
> a source of requirements, not a hard spec: where the repo docs (`CLAUDE.md`, `docs/`) differ, the
> repo docs win.

# Project: SignalForge — Comprehensive Signal Engineering Framework

You are the lead architect and developer of **SignalForge**, a large-scale, general-purpose signal generation, processing, analysis, and measurement framework.

The goal is to build a professional-quality, extensible signal engineering library implemented in both **Python and C#/.NET**.

This is intended to become a substantial, long-lived engineering framework, not a small DSP demonstration or collection of disconnected utilities.

## 1. Overall Vision

SignalForge should eventually support virtually every common operation involved in working with analog, digital, RF, and communications signals.

Capabilities should include:

### Signal Generation
- Sine, cosine, square, triangle, sawtooth, pulse, and arbitrary waveforms
- Complex I/Q signal generation
- Noise generation (AWGN, colored noise, phase noise, etc.)
- Multitone signals
- Chirps and frequency sweeps
- Pulse trains and burst signals
- Random and deterministic data sequences
- PRBS and other test patterns
- Configurable impairments
- Composite and multicarrier signals

### Modulation and Demodulation
- AM, FM, PM
- ASK, FSK, PSK
- BPSK, QPSK, OQPSK, 8PSK
- QAM (16/64/256/1024 and extensible)
- GMSK, GFSK, MSK
- OFDM and related multicarrier techniques
- Pulse shaping and matched filtering
- Symbol mapping and demapping
- Carrier recovery
- Timing recovery
- Frequency and phase synchronization
- Channel estimation and equalization
- Soft-decision demodulation

### Signal Processing
- FFT/IFFT and spectral transforms
- Window functions
- FIR/IIR filters
- Filter design
- Resampling and interpolation
- Decimation
- Convolution and correlation
- Digital downconversion/upconversion
- Frequency translation
- Signal mixing
- Power and amplitude normalization
- Complex signal operations
- Time-domain and frequency-domain analysis
- Spectrograms and time-frequency representations

### RF and Communications Measurements
- RMS, peak, average, and integrated power
- Power spectral density
- Occupied bandwidth
- Channel power
- Adjacent channel leakage/power ratio (ACLR/ACPR)
- Spectrum emission masks
- EVM (RMS, peak, per-symbol, per-subcarrier)
- Frequency error
- Phase error
- IQ imbalance
- DC offset
- Carrier leakage
- Harmonic distortion
- THD and THD+N
- SINAD, SNR, SNDR
- SFDR
- IP2/IP3, including two-tone measurements
- Intermodulation distortion
- Compression measurements such as P1dB
- CCDF and PAPR
- Frequency response
- Group delay
- Phase noise and integrated phase noise
- Modulation accuracy
- BER, SER, PER, and related metrics

### Communications Standards
Eventually provide signal generation, decoding, analysis, and measurements based on publicly available technical specifications for technologies including:

- Bluetooth Classic
- Bluetooth Low Energy
- Wi-Fi (802.11 families)
- CDMA and WCDMA
- LTE
- 5G NR
- GNSS
- Other common wireless and wired communication technologies

Standards support must be modular, versioned, and based on documented specifications.

Do not assume that every standards document is freely redistributable or that every specification can be implemented without additional licensing considerations.

### Data Formats and Interoperability
- Real and complex sample buffers
- Interleaved and planar I/Q
- Common numeric formats (float32, float64, complex64, complex128, int16, etc.)
- Raw binary sample files
- WAV where appropriate
- SigMF
- CSV and NumPy formats
- Configurable byte order, scaling, and metadata
- Streaming and chunk-based processing
- Sample-rate and frequency metadata
- Unit-aware measurements

Eventually support hardware integration, including SDRs, RF instruments, spectrum analyzers, and signal generators. However, keep hardware integration separate from the core signal-processing and measurement libraries.

## 2. Two First-Class Implementations

Implement SignalForge in:

1. Python
2. C# using modern .NET

Both implementations must be usable independently.

Do not make either language depend on the other at runtime.

A major goal is to leverage the two ecosystems to complement and validate each other.

For example:

- Python may use NumPy, SciPy, or other suitable permissively licensed libraries.
- C# may use suitable permissively licensed numerical, DSP, and FFT libraries.
- Python may serve as an independent numerical reference for validating C# algorithms.
- C# may provide optimized implementations suitable for production test systems.
- Both implementations must produce equivalent results within documented numerical tolerances.

Prefer shared mathematical definitions, test vectors, expected outputs, and conformance specifications rather than forcing identical internal implementations.

Design a shared cross-language validation system.

## 3. Open-Source Licensing Requirements — STRICT

This requirement is extremely important.

We may use, incorporate, wrap, or depend on existing open-source software, but only when its licensing is extremely permissive.

**Allowed licenses:**
- MIT
- BSD-2-Clause
- BSD-3-Clause
- Apache-2.0
- ISC
- Other similarly permissive licenses only after explicit approval

**Disallowed by default:**
- GPL (any version)
- LGPL (any version)
- AGPL
- MPL
- EPL
- CDDL
- SSPL
- Any copyleft or reciprocal licensing
- Source-available licenses that are not genuinely open source
- Custom licenses with unclear restrictions
- Unlicensed source code

Do not introduce a dependency under a disallowed or unverified license.

This applies to:
- Runtime dependencies
- Build dependencies
- Test dependencies
- Native libraries
- Transitive dependencies
- Copied source code
- Generated code with licensing restrictions
- Optional components and plugins

When evaluating a library, investigate:
1. Its actual license.
2. Its transitive dependencies.
3. Whether its license applies differently to optional components.
4. Whether commercial and proprietary usage is permitted.
5. Whether redistribution is permitted.
6. Whether attribution or NOTICE files are required.
7. Whether there are patent-related conditions.
8. Whether there are compatibility concerns.

Apache-2.0 is allowed, but its NOTICE, attribution, and other license obligations must be respected.

Maintain a third-party dependency inventory documenting license, version, source repository, usage, and required notices.

Do not simply trust a package description claiming a library is MIT or Apache licensed. Verify authoritative license information when possible.

If licensing cannot be verified, mark the candidate as unapproved and do not integrate it.

Do not copy code from Stack Overflow, GitHub, standards documents, or other sources without verifying reuse rights.

Do not assume that a public specification is public-domain software.

## 4. Research Existing Libraries Before Reimplementing

Before implementing substantial functionality, research existing libraries and determine whether they can be reused.

Consider candidates such as:

**Python**
- NumPy
- SciPy
- NumPy-based signal processing packages
- Specialized communications libraries
- Signal format libraries
- Other relevant numerical libraries

**C#/.NET**
- Math.NET Numerics
- Suitable FFT implementations
- Suitable DSP/filtering libraries
- Other numerical and communications packages

Also investigate specialized open-source signal-processing projects that may provide reusable algorithms, reference implementations, or test vectors.

These are research candidates, not preapproved dependencies.

Do not assume that a library is acceptable merely because it is widely used or available on GitHub.

For each candidate, document:
- Capabilities
- License and verification source
- Dependencies
- Performance considerations
- Maintenance status
- Advantages and disadvantages
- Whether to use, wrap, adapt, or reject it

Prefer leveraging mature, permissively licensed numerical implementations instead of needlessly rewriting fundamental algorithms.

However, avoid making SignalForge merely a thin wrapper around a random collection of libraries.

SignalForge should expose a consistent, well-designed API with predictable behavior.

## 5. Architecture

Design a modular architecture with clear separation of concerns.

Suggested conceptual modules:

- SignalForge.Core
- SignalForge.Numerics
- SignalForge.Waveforms
- SignalForge.DSP
- SignalForge.Modulation
- SignalForge.Demodulation
- SignalForge.Measurements
- SignalForge.RF
- SignalForge.Communications
- SignalForge.Standards
- SignalForge.IO
- SignalForge.Streaming
- SignalForge.Hardware (future)
- SignalForge.Validation

These are conceptual boundaries, not mandatory package names. Improve the architecture if appropriate.

Use a consistent public API across Python and C# where practical, while respecting each language's conventions.

### Signal Representation

Create well-designed abstractions for signals.

Consider:
- Real and complex sample arrays
- Sample rate
- Center frequency
- Time origin
- Units
- Impedance where applicable
- Signal metadata
- Optional calibration information
- Streaming versus finite signals

Avoid forcing unnecessary allocations or metadata overhead onto low-level numerical operations.

Support both high-level convenient operations and low-level performance-oriented APIs.

### Measurement Results

Measurement APIs should return structured results rather than just raw numbers when additional information is meaningful.

For example, an occupied-bandwidth measurement might include:
- Measured bandwidth
- Lower frequency boundary
- Upper frequency boundary
- Occupied power percentage
- Measurement configuration
- Relevant units

Measurement results should be suitable for automated testing, serialization, reporting, and comparison against limits.

### Units and Conventions

Define explicit conventions for:
- Hz, kHz, MHz, GHz
- Linear power versus dB
- dBm, dBW, dBc, dBFS
- Voltage and power relationships
- Reference impedance
- RMS versus peak amplitude
- One-sided versus two-sided spectra
- FFT normalization
- PSD units
- Complex baseband conventions
- Frequency axis conventions
- Symbol and bit ordering
- IQ ordering and sign conventions

Do not permit ambiguous definitions to spread throughout the library.

## 6. Engineering Quality

Treat this as production engineering software.

Requirements:
- Strong automated testing
- Deterministic test vectors
- Reproducible random seeds
- Cross-language conformance tests
- Numerical tolerance specifications
- Boundary and error-case testing
- Performance benchmarks
- Clear documentation
- Examples for major functionality
- Minimal unnecessary allocations
- Support for large sample buffers
- Appropriate streaming interfaces
- Stable public APIs
- Versioned behavior where necessary

Use double precision where numerical accuracy matters, but support single precision for large datasets and performance-sensitive workloads.

Do not optimize prematurely, but design interfaces that permit future SIMD, GPU, multithreading, and native acceleration.

Avoid unnecessary dependencies and unnecessary abstraction layers.

## 7. Numerical and Measurement Correctness

Correctness is critical.

RF and communications measurements frequently depend on detailed conventions, filters, reference waveforms, bandwidths, synchronization, and standards-specific requirements.

For every measurement algorithm:

1. Define the mathematical operation.
2. Document assumptions.
3. Define units and normalization.
4. Document relevant configuration parameters.
5. Establish independent reference results.
6. Test against known analytical cases.
7. Test against independent implementations where possible.
8. Define numerical tolerances.
9. Identify limitations and edge cases.

Do not assume that two algorithms with the same measurement name are interchangeable.

For example, EVM may differ depending on:
- Reference signal construction
- Equalization
- Frequency offset correction
- Timing synchronization
- Normalization
- Measurement window
- Standard-specific definitions

Separate general-purpose measurements from standards-specific measurement procedures.

Never claim compliance with a particular communications standard unless the implementation and validation actually support that claim.

## 8. Cross-Language Testing Strategy

Build a shared conformance test system.

Use language-neutral test vectors and expected results.

Possible approach:

- Shared JSON metadata
- Binary sample files for larger vectors
- Deterministic generated test vectors
- Expected measurement results
- Defined absolute and relative tolerances

The Python and C# implementations should execute the same test cases.

Where appropriate, create additional integration tests that:

1. Generate signals in Python.
2. Analyze them in C#.
3. Generate signals in C#.
4. Analyze them in Python.
5. Compare measurements and waveforms.
6. Report discrepancies.

Avoid using one implementation as the sole source of truth.

Use analytical reference cases, published numerical examples, or independently validated third-party implementations wherever possible.

A shared bug in two implementations must not be mistaken for correctness.

## 9. Repository Structure

Propose a clean monorepo containing:

- Python implementation
- C# implementation
- Shared test vectors
- Cross-language validation tooling
- Documentation
- Examples
- Benchmarks
- Dependency/license inventory
- Architecture decision records

Use modern Python packaging and modern .NET project conventions.

Include appropriate automated build, test, formatting, and static analysis workflows.

Make it easy to run either implementation independently.

## 10. Development Approach

Do not attempt to implement the entire library immediately.

This is a large project that should be developed incrementally.

**Phase 1 — Research and architecture**

- Inspect the repository.
- Research relevant permissively licensed dependencies.
- Establish license verification rules.
- Propose the architecture.
- Define numerical conventions.
- Define the shared test strategy.
- Identify major technical risks.
- Create a prioritized development roadmap.

**Phase 2 — Foundation**

Implement:
- Repository structure
- Python and C# projects
- Shared signal representations
- Basic numerical operations
- Unit conversion utilities
- Shared test vector infrastructure
- Automated tests
- Initial documentation

**Phase 3 — First vertical slice**

Implement an end-to-end demonstration in both languages involving:

1. Generate a deterministic complex QPSK signal.
2. Apply configurable pulse shaping.
3. Add controlled AWGN and frequency offset.
4. Recover or compensate for known impairments.
5. Demodulate the signal.
6. Calculate EVM.
7. Calculate BER.
8. Calculate occupied bandwidth.
9. Compare Python and C# results.
10. Produce a machine-readable validation report.

Use clearly documented assumptions.

Initially, known-parameter compensation is acceptable, provided it is distinguished from blind synchronization and recovery.

Do not fake receiver functionality by silently using original transmitted symbols as recovered symbols.

**Phase 4 — Expansion**

Expand incrementally into:
- Additional modulation formats
- Filters and DSP operations
- RF measurements
- Signal impairments
- Streaming
- Standards-specific signal generators and analyzers
- Performance optimization
- Hardware interfaces

## 11. Important Design Principles

- Correctness over cleverness.
- Prefer reusable implementations over unnecessary reinvention.
- Strict permissive-license compliance.
- Python and C# are equal citizens.
- No Python runtime dependency for C#.
- No C# runtime dependency for Python.
- Shared tests and specifications.
- Consistent numerical behavior.
- Avoid unnecessary complexity.
- Make individual modules independently usable.
- Keep standards-specific behavior separate from generic algorithms.
- Build for long-term maintainability.
- Favor practical, working engineering code over excessive architecture.
- Do not create hundreds of placeholder classes.
- Do not silently substitute approximations for standards-defined measurements.
- Document what is implemented versus planned.

## 12. Your Immediate Assignment

Start by examining the existing repository and determining whether anything already exists.

Then:

1. Research suitable open-source dependencies and verify their licenses.
2. Create an initial architecture proposal.
3. Create a dependency evaluation document.
4. Define the core signal and measurement data models.
5. Define shared numerical conventions.
6. Propose the initial repository structure.
7. Establish the testing and cross-language validation strategy.
8. Create a prioritized implementation roadmap.
9. Implement the foundational project scaffolding and the first small set of meaningful, tested operations.
10. Run the available builds and tests and report actual results.

Do not spend the entire effort writing plans. Produce working code after establishing the necessary architecture.

Do not attempt to implement all the requested features in one pass.

When uncertain about a significant architectural decision, present the tradeoffs and make a recommendation.

Keep the implementation clean, practical, and extensible.

**Begin with the architecture and dependency research, then proceed into the initial implementation.**
