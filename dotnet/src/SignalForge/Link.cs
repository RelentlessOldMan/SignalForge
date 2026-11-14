using System.Globalization;
using System.Numerics;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SignalForge;

/// <summary>One QPSK link run. Definitions in docs/conventions.md (QPSK link).</summary>
public sealed record QpskLinkConfig
{
    /// <summary>Symbols in the frame, at least 2.</summary>
    public required int NumSymbols { get; init; }

    /// <summary>Eb/N0 in dB; null means no noise.</summary>
    public double? EbN0Db { get; init; }

    /// <summary>Symbol rate in Hz.</summary>
    public double SymbolRate { get; init; } = 1000;

    /// <summary>Samples per symbol, at least 2.</summary>
    public int SamplesPerSymbol { get; init; } = 4;

    /// <summary>Root-raised-cosine roll-off.</summary>
    public double Rolloff { get; init; } = 0.35;

    /// <summary>Filter span in symbols.</summary>
    public int SpanSymbols { get; init; } = 10;

    /// <summary>Channel delay in samples.</summary>
    public int DelaySamples { get; init; }

    /// <summary>Channel carrier frequency offset in Hz.</summary>
    public double FrequencyOffsetHz { get; init; }

    /// <summary>Channel carrier phase in radians.</summary>
    public double Phase { get; init; }

    /// <summary>Known symbols at the frame start, 1 to <see cref="NumSymbols"/>.</summary>
    public int PreambleSymbols { get; init; } = 32;

    /// <summary>Symbols per block for the fine phase estimate, at least 1.</summary>
    public int PhaseBlockSymbols { get; init; } = 32;

    /// <summary>PRBS order of the payload.</summary>
    public int PrbsOrder { get; init; } = 15;

    /// <summary>Noise seed.</summary>
    public int Seed { get; init; }

    /// <summary>"qpsk", "qam16", "psk8", "qam64", "fsk2", "fsk4" or "ofdm".</summary>
    public string Modulation { get; init; } = "qpsk";

    /// <summary>Wiener phase noise linewidth in Hz, at least 0; 0 adds none.</summary>
    public double PhaseNoiseLinewidthHz { get; init; }

    /// <summary>Receiver sample clock offset in parts per million, within ±1e5.</summary>
    public double ClockOffsetPpm { get; init; }

    /// <summary>Gardner timing loop gains [kp, ki], both at least 0; null samples at the block
    /// timing estimate.</summary>
    public IReadOnlyList<double>? TimingLoopGains { get; init; }

    /// <summary>QPSK carrier loop gains [kp, ki], both at least 0; null runs no carrier
    /// loop.</summary>
    public IReadOnlyList<double>? CarrierLoopGains { get; init; }

    /// <summary>OFDM DFT size, at least 2; checked for every modulation, used by "ofdm" only.</summary>
    public int OfdmNfft { get; init; } = 64;

    /// <summary>OFDM cyclic prefix length, 1 to <see cref="OfdmNfft"/>.</summary>
    public int OfdmCpLen { get; init; } = 16;

    /// <summary>OFDM used subcarriers, distinct signed indices as <see cref="Modulation.OfdmModulate"/> takes
    /// them; null for every one but 0.</summary>
    public IReadOnlyList<int>? OfdmSubcarriers { get; init; }

    /// <summary>Multipath path delays in samples, each at least 0; null [the default] for none, else
    /// as many as <see cref="MultipathGains"/>. "ofdm" (at most half of <see cref="OfdmCpLen"/>), or a
    /// single-carrier modulation with <see cref="EqualizerTaps"/>.</summary>
    public IReadOnlyList<int>? MultipathDelays { get; init; }

    /// <summary>Multipath path gains, each a finite pair [re, im]; null exactly when
    /// <see cref="MultipathDelays"/> is null.</summary>
    public IReadOnlyList<IReadOnlyList<double>>? MultipathGains { get; init; }

    /// <summary>LMS equalizer taps, at least 1, for the single-carrier modulations; null [the default]
    /// for no equalizer (ADR 0067).</summary>
    public int? EqualizerTaps { get; init; }

    /// <summary>The equalizer's normalized step, 0 to 2.</summary>
    public double EqualizerStep { get; init; } = 0.1;

    /// <summary>Decision-feedback taps on the equalizer, at the symbol rate; not negative, nonzero
    /// only with <see cref="EqualizerTaps"/>; 0 [the default] for a linear equalizer (ADR 0070).</summary>
    public int EqualizerFeedback { get; init; }
}

/// <summary>What the receiver estimated and measured on one link run.</summary>
/// <param name="Config">The run's configuration.</param>
/// <param name="TimingOffset">Symbol timing estimate in samples, in [0, sps).</param>
/// <param name="FrameStart">Frame start in symbols into the sampled stream.</param>
/// <param name="FrequencyOffsetHz">Carrier frequency estimate in Hz; null for FSK.</param>
/// <param name="PhaseOffset">Carrier phase at the frame's first symbol in radians, in (−π, π]; null
/// for FSK.</param>
/// <param name="Evm">EVM of the recovered symbols; null for FSK.</param>
/// <param name="BitErrors">Bit errors over the frame, preamble included.</param>
/// <param name="BerTheory">Theoretical BER at the configured Eb/N0; null without noise.</param>
public sealed record QpskLinkReport(
    QpskLinkConfig Config,
    double TimingOffset,
    int FrameStart,
    double? FrequencyOffsetHz,
    double? PhaseOffset,
    Evm? Evm,
    ErrorCount BitErrors,
    double? BerTheory)
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = true,
        Converters = { new NamedNonFiniteConverter() },
    };

    /// <summary>The report as JSON: snake_case names, non-finite numbers as "inf", "-inf", "nan".</summary>
    public string ToJson() => JsonSerializer.Serialize(this, JsonOptions);

    private sealed class NamedNonFiniteConverter : JsonConverter<double>
    {
        public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
            reader.TokenType == JsonTokenType.String
                ? reader.GetString() switch
                {
                    "inf" => double.PositiveInfinity,
                    "-inf" => double.NegativeInfinity,
                    "nan" => double.NaN,
                    var s => double.Parse(s!, CultureInfo.InvariantCulture),
                }
                : reader.GetDouble();

        public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options)
        {
            if (double.IsFinite(value))
                writer.WriteNumberValue(value);
            else
                writer.WriteStringValue(double.IsNaN(value) ? "nan" : value > 0 ? "inf" : "-inf");
        }
    }
}

/// <summary>End-to-end link (QPSK, QAM, 8-PSK, FSK, OFDM): bits, shaping, channel, recovery, EVM and
/// BER.</summary>
public static class Link
{
    /// <summary>Runs one shaped QPSK link through delay, carrier offset, phase noise, clock offset
    /// and AWGN,
    /// then recovers it (conventions: QPSK link).</summary>
    /// <param name="config">The run; see <see cref="QpskLinkConfig"/>.</param>
    public static QpskLinkReport QpskLink(QpskLinkConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);
        var c = config;
        int n = c.NumSymbols, sps = c.SamplesPerSymbol, pre = c.PreambleSymbols, blk = c.PhaseBlockSymbols;
        ArgumentOutOfRangeException.ThrowIfLessThan(n, 2, nameof(config));
        ArgumentOutOfRangeException.ThrowIfLessThan(sps, 2, nameof(config));
        ArgumentOutOfRangeException.ThrowIfNegative(c.SpanSymbols, nameof(config));
        ArgumentOutOfRangeException.ThrowIfNegative(c.DelaySamples, nameof(config));
        ArgumentOutOfRangeException.ThrowIfNegative(c.Seed, nameof(config));
        if (pre < 1 || pre > n)
            throw new ArgumentOutOfRangeException(nameof(config), pre, "PreambleSymbols must be between 1 and NumSymbols");
        ArgumentOutOfRangeException.ThrowIfLessThan(blk, 1, nameof(config));
        double rs = Check.PositiveFinite(c.SymbolRate, nameof(config));
        if (!double.IsFinite(c.FrequencyOffsetHz) || !double.IsFinite(c.Phase) || c.EbN0Db is { } e && !double.IsFinite(e))
            throw new ArgumentOutOfRangeException(nameof(config), "numbers must be finite");
        // 0 QPSK, 1 16-QAM, 2 8-PSK, 3 64-QAM, 4 2-FSK, 5 4-FSK
        int mod = c.Modulation switch
        {
            "qpsk" => 0,
            "qam16" => 1,
            "psk8" => 2,
            "qam64" => 3,
            "fsk2" => 4,
            "fsk4" => 5,
            "ofdm" => 6,
            _ => throw new ArgumentException(
                "Modulation must be \"fsk2\", \"fsk4\", \"ofdm\", \"psk8\", \"qam16\", \"qam64\" or \"qpsk\"", nameof(config)),
        };
        int bps = mod switch { 1 => 4, 2 => 3, 3 => 6, _ => 2 };
        double step = mod == 2 ? Math.PI / 4 : Math.PI / 2;
        if (!(c.PhaseNoiseLinewidthHz >= 0) || !double.IsFinite(c.PhaseNoiseLinewidthHz))
            throw new ArgumentOutOfRangeException(nameof(config), c.PhaseNoiseLinewidthHz, "PhaseNoiseLinewidthHz must be finite and at least 0");
        if (!(Math.Abs(c.ClockOffsetPpm) <= 1e5))
            throw new ArgumentOutOfRangeException(nameof(config), c.ClockOffsetPpm, "ClockOffsetPpm must be finite and within 1e5");
        Gains(c.TimingLoopGains, nameof(c.TimingLoopGains), nameof(config));
        Gains(c.CarrierLoopGains, nameof(c.CarrierLoopGains), nameof(config));
        int[] subcarriers = OfdmSubcarriersOf(c);
        Complex[]? paths = MultipathGainsOf(c);
        ArgumentOutOfRangeException.ThrowIfNegative(c.EqualizerFeedback, nameof(config));
        if (c.EqualizerFeedback > 0 && c.EqualizerTaps is null)
            throw new ArgumentException("EqualizerFeedback needs EqualizerTaps", nameof(config));
        if (c.EqualizerTaps is { } et)
        {
            ArgumentOutOfRangeException.ThrowIfLessThan(et, 1, nameof(config));
            if (!(c.EqualizerStep >= 0 && c.EqualizerStep <= 2))
                throw new ArgumentOutOfRangeException(nameof(config), c.EqualizerStep, "EqualizerStep must be between 0 and 2");
            if (mod >= 4)
                throw new ArgumentException("EqualizerTaps is for the single-carrier modulations only", nameof(config));
            if (sps % 2 != 0)
                throw new ArgumentException("the equalizer needs an even SamplesPerSymbol", nameof(config));
            if (pre >= n)
                throw new ArgumentException("the equalizer needs PreambleSymbols below NumSymbols", nameof(config));
            if (c.TimingLoopGains is not null || c.CarrierLoopGains is not null)
                throw new ArgumentException("the equalizer takes no TimingLoopGains or CarrierLoopGains", nameof(config));
        }
        else
        {
            if (!(c.EqualizerStep >= 0 && c.EqualizerStep <= 2))
                throw new ArgumentOutOfRangeException(nameof(config), c.EqualizerStep, "EqualizerStep must be between 0 and 2");
            if (paths is not null && mod != 6)
                throw new ArgumentException("MultipathDelays and MultipathGains need ofdm or EqualizerTaps", nameof(config));
        }
        if (mod == 6)
            return OfdmLink(c, subcarriers);
        if (mod >= 4)
            return FskLink(c, mod == 4 ? 2 : 4);

        // transmitter
        byte[] bits = Waveforms.Prbs(c.PrbsOrder, bps * n);
        Complex[] a = mod switch
        {
            1 => SignalForge.Modulation.Qam16Map(bits),
            2 => SignalForge.Modulation.Psk8Map(bits),
            3 => SignalForge.Modulation.Qam64Map(bits),
            _ => SignalForge.Modulation.QpskMap(bits),
        };
        double[] h = Dsp.RrcTaps(c.Rolloff, sps, c.SpanSymbols);
        Complex[] shaped = Dsp.PulseShape(a, h, sps);
        int spread = paths is null ? 0 : c.MultipathDelays!.Max();
        var tx = new Complex[c.DelaySamples + shaped.Length + spread];
        shaped.CopyTo(tx, c.DelaySamples);
        if (paths is not null)
            tx = Channel.Multipath(tx, [.. c.MultipathDelays!], paths);
        Complex[] rx = ChannelOf(c, tx, bps, 1.0 / sps);
        // receiver
        Complex[] y = Dsp.Convolve(rx, h);
        double tau = Sync.TimingOffset(y, sps);
        Complex[] r;
        if (c.TimingLoopGains is { } tg)
            r = Sync.GardnerTiming(y, sps, tg[0], tg[1], tau).Symbols;
        else
        {
            int p = (int)Math.Round(tau) % sps;
            r = new Complex[(y.Length - p + sps - 1) / sps];
            for (int k = 0; k < r.Length; k++)
                r[k] = y[p + k * sps];
        }
        double f = mod switch
        {
            1 or 3 => Sync.PowerFrequencyOffset(r, rs, 4),
            2 => Sync.PowerFrequencyOffset(r, rs, 8),
            _ => Sync.QpskFrequencyOffset(r, rs),
        };
        double f1 = f;
        // frame start: the first maximum of the preamble correlation, its blocks' magnitudes added so
        // a residual frequency error cannot turn a long preamble through a cycle (ADR 0068)
        Complex[] cr = Channel.FrequencyOffset(r, -f, rs);
        int k0 = 0;
        double best = -1;
        for (int k = 0; k <= cr.Length - n; k++)
        {
            double q = 0;
            for (int b0 = 0; b0 < pre; b0 += blk)
            {
                Complex s = Complex.Zero;
                for (int i = b0; i < Math.Min(b0 + blk, pre); i++)
                    s += Complex.Conjugate(a[i]) * cr[k + i];
                q += s.Magnitude;
            }
            if (q > best)
                (best, k0) = (q, k);
        }
        // fine frequency and phase: a line through the unwrapped block phases at each block's middle
        Complex[] z = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs);
        double[] ph = mod == 2 ? Sync.Psk8BlockPhases(z, blk) : Sync.QpskBlockPhases(z, blk);
        double slope = 0, phi = ph[0];
        if (ph.Length > 1)
        {
            var x = new double[ph.Length];
            for (int b = 0; b < ph.Length; b++)
                x[b] = (b * blk + Math.Min((b + 1) * blk, n) - 1) / 2.0;
            double xm = x.Average(), ym = ph.Average(), sxy = 0, sxx = 0;
            for (int b = 0; b < ph.Length; b++)
            {
                sxy += (x[b] - xm) * (ph[b] - ym);
                sxx += (x[b] - xm) * (x[b] - xm);
            }
            slope = sxy / sxx;
            phi = ym - slope * xm;
        }
        f += slope * rs / (2 * Math.PI);
        // the preamble resolves the π/2 (8-PSK: π/4) ambiguity
        Complex[] zp = Channel.FrequencyOffset(z.AsSpan(0, pre), -slope * rs / (2 * Math.PI), rs, -phi);
        Complex cp = Complex.Zero;
        for (int i = 0; i < pre; i++)
            cp += Complex.Conjugate(a[i]) * zp[i];
        phi = Wrap(phi + step * Math.Round(Math.Atan2(cp.Imaginary, cp.Real) / step));
        if (c.EqualizerTaps is { } taps)
        {
            int nb = pre / blk;
            if (nb >= 2)
            {
                // the frequency from the preamble's known symbols: a line through its full blocks'
                // phases, far less hurt by interference than the blind estimators (ADR 0070)
                var th = new double[nb];
                Complex prev = Complex.Zero;
                for (int b = 0; b < nb; b++)
                {
                    Complex q = Complex.Zero;
                    for (int i = b * blk; i < (b + 1) * blk; i++)
                        q += Complex.Conjugate(a[i]) * cr[k0 + i];
                    if (b == 0)
                    {
                        th[0] = Math.Atan2(q.Imaginary, q.Real);
                    }
                    else
                    {
                        Complex t = q * Complex.Conjugate(prev);
                        th[b] = th[b - 1] + Math.Atan2(t.Imaginary, t.Real);
                    }
                    prev = q;
                }
                double xm = (nb - 1) * blk / 2.0, ym = th.Average(), sxy = 0, sxx = 0;
                for (int b = 0; b < nb; b++)
                {
                    sxy += (b * blk - xm) * (th[b] - ym);
                    sxx += (b * blk - xm) * (b * blk - xm);
                }
                f = f1 + sxy / sxx * rs / (2 * Math.PI);
            }
            // fractionally spaced at 2 per symbol, its center on the sample the chain takes (ADR 0067)
            Complex[] v = Channel.FrequencyOffset(y, -f, rs * sps);
            int s0 = (int)Math.Round(tau) % sps + k0 * sps, half = sps / 2;
            var xe = new Complex[2 * n];
            for (int m = 0; m < xe.Length && s0 + m * half < v.Length; m++)
                xe[m] = v[s0 + m * half];
            Complex[] eq = Sync.DfeEqualizer(xe, a.AsSpan(0, pre), taps, c.EqualizerFeedback, c.EqualizerStep, 2, null, c.Modulation).Symbols;
            // the preamble is the equalizer's training, so it does not count
            z = eq[pre..];
            a = a[pre..];
            bits = bits[(bps * pre)..];
        }
        else if (c.CarrierLoopGains is { } cg)
        {
            Complex[] w = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs);
            Complex cw = Complex.Zero;
            for (int i = 0; i < pre; i++)
                cw += Complex.Conjugate(a[i]) * w[i];
            double start = Math.Atan2(cw.Imaginary, cw.Real);
            z = (mod switch
            {
                1 => Sync.Qam16CarrierTracking(w, cg[0], cg[1], start),
                2 => Sync.Psk8CarrierTracking(w, cg[0], cg[1], start),
                3 => Sync.Qam64CarrierTracking(w, cg[0], cg[1], start),
                _ => Sync.QpskCarrierTracking(w, cg[0], cg[1], start),
            }).Symbols;
        }
        else
            z = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs, -phi);

        byte[] got = mod switch
        {
            1 => SignalForge.Modulation.Qam16DemapHard(z),
            2 => SignalForge.Modulation.Psk8DemapHard(z),
            3 => SignalForge.Modulation.Qam64DemapHard(z),
            _ => SignalForge.Modulation.QpskDemapHard(z),
        };
        double eh = PulseEnergy(c, paths);
        double? theory = c.EbN0Db is not { } eb ? null : eh <= 0 ? 0.5 : mod switch
        {
            1 => Metrics.Qam16BerTheory(eb + 10 * Math.Log10(eh)),
            2 => Metrics.Psk8BerTheory(eb + 10 * Math.Log10(eh)),
            3 => Metrics.Qam64BerTheory(eb + 10 * Math.Log10(eh)),
            _ => Metrics.QpskBerTheory(eb + 10 * Math.Log10(eh)),
        };
        return new QpskLinkReport(c, tau, k0, f, phi, Metrics.Evm(z, a), Metrics.BitErrors(bits, got), theory);
    }

    // E_h, the energy the multipath paths give one pulse, 1 without multipath: with it the theory is
    // the matched-filter bound (conventions: QPSK link, Report)
    private static double PulseEnergy(QpskLinkConfig c, Complex[]? paths)
    {
        if (paths is null)
            return 1;
        double beta = c.Rolloff, e = 0;
        double Rho(double t) // raised cosine at t symbols
        {
            double sinc = t == 0 ? 1 : Math.Sin(Math.PI * t) / (Math.PI * t);
            if (beta > 0 && Math.Abs(t) == 1 / (2 * beta))
                return Math.PI / 4 * Math.Sin(Math.PI / (2 * beta)) / (Math.PI / (2 * beta));
            return sinc * Math.Cos(Math.PI * beta * t) / (1 - (2 * beta * t) * (2 * beta * t));
        }
        for (int i = 0; i < paths.Length; i++)
            for (int j = 0; j < paths.Length; j++)
                e += (paths[i] * Complex.Conjugate(paths[j])).Real * Rho((double)(c.MultipathDelays![j] - c.MultipathDelays[i]) / c.SamplesPerSymbol);
        return e;
    }

    // carrier offset, phase noise, clock offset and AWGN (conventions: QPSK link, Channel)
    private static Complex[] ChannelOf(QpskLinkConfig c, Complex[] tx, int bps, double signalPower)
    {
        double fs = c.SymbolRate * c.SamplesPerSymbol;
        Complex[] rx = Channel.FrequencyOffset(tx, c.FrequencyOffsetHz, fs, c.Phase);
        var rng = new Random(c.Seed);
        if (c.PhaseNoiseLinewidthHz > 0)
            rx = Channel.PhaseNoise(rx, c.PhaseNoiseLinewidthHz, fs, rng);
        if (c.ClockOffsetPpm != 0)
            rx = Channel.ClockOffset(rx, c.ClockOffsetPpm);
        if (c.EbN0Db is { } ebN0Db)
            rx = Channel.Awgn(rx, ebN0Db + 10 * Math.Log10(bps), c.SamplesPerSymbol, rng, signalPower);
        return rx;
    }

    // the FSK link (conventions: QPSK link, FSK; ADR 0057)
    private static QpskLinkReport FskLink(QpskLinkConfig c, int m)
    {
        int n = c.NumSymbols, sps = c.SamplesPerSymbol, pre = c.PreambleSymbols;
        if (sps < m)
            throw new ArgumentOutOfRangeException(nameof(c), sps, $"{c.Modulation} needs SamplesPerSymbol of at least {m}");
        if (c.TimingLoopGains is not null || c.CarrierLoopGains is not null)
            throw new ArgumentException($"{c.Modulation} takes no TimingLoopGains or CarrierLoopGains", nameof(c));
        Dsp.RrcTaps(c.Rolloff, sps, c.SpanSymbols); // checked as for the other modulations
        int k = m == 2 ? 1 : 2;
        byte[] bits = Waveforms.Prbs(c.PrbsOrder, k * n);
        Complex[] fsk = SignalForge.Modulation.FskModulate(bits, m, sps, 1);
        var tx = new Complex[c.DelaySamples + fsk.Length];
        fsk.CopyTo(tx, c.DelaySamples);
        Complex[] rx = ChannelOf(c, tx, k, 1);
        if (rx.Length < tx.Length + sps)
            Array.Resize(ref rx, tx.Length + sps);
        // row l is tone level 2l - (m - 1)
        var re = new double[m, sps];
        var im = new double[m, sps];
        for (int l = 0; l < m; l++)
            for (int t = 0; t < sps; t++)
            {
                double psi = Math.PI * ((2 * l - (m - 1)) * t / (double)sps);
                (re[l, t], im[l, t]) = (Math.Cos(psi), -Math.Sin(psi));
            }
        // timing: the sample phase with the most detector energy over the whole stream
        int tau = 0;
        double bestG = -1;
        for (int t = 0; t < sps; t++)
        {
            double g = 0;
            for (int d = t; d + sps <= rx.Length; d += sps)
            {
                double top = 0;
                for (int l = 0; l < m; l++)
                    top = Math.Max(top, Energy(rx, d, l, re, im));
                g += top;
            }
            if (g > bestG)
                (bestG, tau) = (g, t);
        }
        // frame: the offset at that phase with the most energy in the preamble's known tones
        var labels = new int[pre];
        for (int i = 0; i < pre; i++)
            for (int j = 0; j < k; j++)
                labels[i] = 2 * labels[i] + bits[i * k + j];
        int d0 = tau;
        double best = -1;
        for (int d = tau; d <= rx.Length - n * sps; d += sps)
        {
            double q = 0;
            for (int i = 0; i < pre; i++)
                q += Energy(rx, d + i * sps, labels[i], re, im);
            if (q > best)
                (best, d0) = (q, d);
        }
        byte[] got = SignalForge.Modulation.FskDemodNoncoherent(rx.AsSpan(d0, n * sps), m, sps, 1);
        double? theory = c.EbN0Db is { } eb ? Metrics.FskBerTheory(eb, m) : null;
        return new QpskLinkReport(c, d0 % sps, d0 / sps, null, null, null, Metrics.BitErrors(bits, got), theory);
    }

    // the OFDM fields, checked for every modulation; the used subcarriers (conventions: QPSK link, OFDM)
    private static int[] OfdmSubcarriersOf(QpskLinkConfig c)
    {
        int n = c.OfdmNfft, low = -(n / 2);
        ArgumentOutOfRangeException.ThrowIfLessThan(n, 2, nameof(c));
        if (c.OfdmCpLen < 1 || c.OfdmCpLen > n)
            throw new ArgumentOutOfRangeException(nameof(c), c.OfdmCpLen, "OfdmCpLen must be between 1 and OfdmNfft");
        if (c.OfdmSubcarriers is null)
            return [.. Enumerable.Range(low, n).Where(k => k != 0)];
        int[] k = [.. c.OfdmSubcarriers];
        if (k.Length == 0 || k.Any(v => v < low || v > low + n - 1) || k.Distinct().Count() != k.Length)
            throw new ArgumentException($"OfdmSubcarriers must be distinct indices in {low} ... {low + n - 1}, at least one", nameof(c));
        return k;
    }

    // the multipath fields, checked for every modulation; the gains, or null (ADR 0064)
    private static Complex[]? MultipathGainsOf(QpskLinkConfig c)
    {
        IReadOnlyList<int>? dl = c.MultipathDelays;
        IReadOnlyList<IReadOnlyList<double>>? gl = c.MultipathGains;
        if (dl is null && gl is null)
            return null;
        if (dl is null || gl is null || dl.Count != gl.Count || dl.Count == 0)
            throw new ArgumentException("MultipathDelays and MultipathGains must both be null or of equal non-zero length", nameof(c));
        if (dl.Any(d => d < 0))
            throw new ArgumentOutOfRangeException(nameof(c), "MultipathDelays must be at least 0");
        var g = new Complex[gl.Count];
        for (int i = 0; i < g.Length; i++)
        {
            if (gl[i] is not { Count: 2 } pair)
                throw new ArgumentException("MultipathGains must be pairs [re, im]", nameof(c));
            if (!double.IsFinite(pair[0]) || !double.IsFinite(pair[1]))
                throw new ArgumentOutOfRangeException(nameof(c), "MultipathGains must be finite");
            g[i] = new Complex(pair[0], pair[1]);
        }
        return g;
    }

    // the OFDM link (conventions: QPSK link, OFDM; ADR 0063, 0064)
    private static QpskLinkReport OfdmLink(QpskLinkConfig c, int[] k)
    {
        int nf = c.OfdmNfft, cp = c.OfdmCpLen, sps = c.SamplesPerSymbol, u = k.Length;
        double fs = c.SymbolRate * sps;
        if (c.NumSymbols % u != 0 || c.PreambleSymbols % u != 0)
            throw new ArgumentException($"NumSymbols and PreambleSymbols must be multiples of {u} (subcarriers)", nameof(c));
        Dsp.RrcTaps(c.Rolloff, sps, c.SpanSymbols); // checked as for the other modulations
        if (c.CarrierLoopGains is not null)
            throw new ArgumentException("ofdm takes no CarrierLoopGains: the block phase is its carrier loop", nameof(c));
        if (!(Math.Abs(c.FrequencyOffsetHz) < fs / (2 * nf)))
            throw new ArgumentOutOfRangeException(nameof(c), c.FrequencyOffsetHz, "ofdm needs |FrequencyOffsetHz| below half a subcarrier spacing");
        Complex[]? paths = MultipathGainsOf(c);
        int[] delays = paths is null ? [] : [.. c.MultipathDelays!];
        int spread = delays.Length > 0 ? delays.Max() : 0;
        if (spread > cp / 2)
            throw new ArgumentOutOfRangeException(nameof(c), "ofdm needs every multipath delay at most half of OfdmCpLen");
        int b = c.NumSymbols / u, p = c.PreambleSymbols / u;
        if (Math.Abs(c.ClockOffsetPpm) * 1e-6 * (c.DelaySamples + (double)b * (nf + cp)) > cp / 2 - spread)
            throw new ArgumentOutOfRangeException(nameof(c), c.ClockOffsetPpm, "ofdm needs the clock drift over the frame within half the prefix");
        byte[] bits = Waveforms.Prbs(c.PrbsOrder, 2 * c.NumSymbols);
        Complex[] a = SignalForge.Modulation.QpskMap(bits);
        Complex[] frame = SignalForge.Modulation.OfdmModulate(a, nf, cp, k);
        // room after the frame for every echo and a slow clock
        var tx = new Complex[c.DelaySamples + frame.Length + cp / 2];
        frame.CopyTo(tx, c.DelaySamples);
        if (paths is not null)
            tx = Channel.Multipath(tx, delays, paths);
        Complex[] rx = ChannelOf(c, tx, 2, 1.0 / sps);
        // 1. timing and frequency from the cyclic prefix
        int length = frame.Length, d0 = 0;
        double best = double.NegativeInfinity;
        Complex gamma = Complex.Zero;
        for (int d = 0; d <= rx.Length - length; d++)
        {
            Complex g = Complex.Zero;
            double phi = 0;
            for (int j = 0; j < b; j++)
                for (int m = 0; m < cp; m++)
                {
                    Complex r0 = rx[d + j * (nf + cp) + m], r1 = rx[d + j * (nf + cp) + m + nf];
                    g += r0 * Complex.Conjugate(r1);
                    phi += r0.Real * r0.Real + r0.Imaginary * r0.Imaginary + r1.Real * r1.Real + r1.Imaginary * r1.Imaginary;
                }
            double metric = g.Magnitude - phi / 2;
            if (metric > best)
                (best, d0, gamma) = (metric, d, g);
        }
        double f = -Math.Atan2(gamma.Imaginary, gamma.Real) * fs / (2 * Math.PI * nf);
        // the block: the prefix ties one block early over leading zeros; the preamble decides
        int np_ = p * (nf + cp), d1 = d0;
        var x = new Complex[np_];
        for (int i = 0; i < np_; i++)
            x[i] = Complex.Conjugate(frame[i]) * Complex.FromPolarCoordinates(1, -2 * Math.PI * f / fs * i);
        best = -1;
        for (int d = d0 % (nf + cp); d <= rx.Length - length; d += nf + cp)
        {
            Complex s = Complex.Zero;
            for (int i = 0; i < np_; i++)
                s += x[i] * rx[d + i];
            if (s.Magnitude > best)
                (best, d1) = (s.Magnitude, d);
        }
        d0 = d1;
        // 2. back off half a prefix, derotate (phase 0 at d0) and demodulate; 3. channel from the
        // preamble blocks
        int d2 = Math.Max(d0 - cp / 2, 0), shift = d0 - d2;
        Complex[] y = Channel.FrequencyOffset(rx.AsSpan(d2, length), -f, fs, 2 * Math.PI * f * shift / fs);
        Complex[] zm = SignalForge.Modulation.OfdmDemodulate(y, nf, cp, k);
        // each preamble block's common phase turned to block 0's before the average: a residual
        // frequency or phase noise would otherwise smear the estimate
        var h = new Complex[u];
        for (int i = 0; i < u; i++)
            h[i] = zm[i] / a[i];
        for (int j = 1; j < p; j++)
        {
            Complex t = Complex.Zero;
            for (int i = 0; i < u; i++)
                t += zm[j * u + i] / a[j * u + i] * Complex.Conjugate(zm[i] / a[i]);
            Complex turn = t == Complex.Zero ? Complex.One : Complex.Conjugate(t) / t.Magnitude;
            for (int i = 0; i < u; i++)
                h[i] += zm[j * u + i] / a[j * u + i] * turn;
        }
        for (int i = 0; i < u; i++)
            h[i] /= p;
        // 4. common phase per block and, with TimingLoopGains, the window offset: on the known
        // symbols through the preamble, then decision-directed
        var z = new Complex[zm.Length];
        var r = new Complex[u];
        var e = new Complex[u];
        double theta = 0, tau = 0, v = 0, kMean = k.Average(), kk = 0;
        foreach (int ki in k)
            kk += (ki - kMean) * (ki - kMean);
        for (int j = 0; j < b; j++)
        {
            for (int i = 0; i < u; i++)
                r[i] = zm[j * u + i] / h[i] * Complex.FromPolarCoordinates(1, -(theta + 2 * Math.PI * k[i] * tau / nf));
            Complex[] q = j < p ? a[(j * u)..((j + 1) * u)] : SignalForge.Modulation.QpskMap(SignalForge.Modulation.QpskDemapHard(r));
            Complex s = Complex.Zero;
            for (int i = 0; i < u; i++)
            {
                e[i] = r[i] * Complex.Conjugate(q[i]);
                s += e[i];
            }
            theta += Math.Atan2(s.Imaginary, s.Real);
            if (c.TimingLoopGains is { } tg && kk > 0)
            {
                double num = 0;
                for (int i = 0; i < u; i++)
                {
                    Complex ph = e[i] * Complex.Conjugate(s);
                    num += (k[i] - kMean) * Math.Atan2(ph.Imaginary, ph.Real);
                }
                double err = nf / (2 * Math.PI) * num / kk;
                v += tg[1] * err;
                tau += tg[0] * err + v;
            }
            for (int i = 0; i < u; i++)
                z[j * u + i] = zm[j * u + i] / h[i] * Complex.FromPolarCoordinates(1, -(theta + 2 * Math.PI * k[i] * tau / nf));
        }
        Complex hs = Complex.Zero;
        for (int i = 0; i < u; i++)
            hs += h[i] * Complex.Exp(new Complex(0, 2 * Math.PI * k[i] * shift / nf));
        byte[] got = SignalForge.Modulation.QpskDemapHard(z);
        double? theory = c.EbN0Db is { } eb ? Metrics.QpskBerTheory(eb) : null;
        if (theory is not null && paths is not null)
        {
            // the mean over subcarriers of the QPSK BER at |H_k|²·Eb/N0, 1/2 where H_k = 0
            double sum = 0;
            for (int i = 0; i < u; i++)
            {
                Complex hk = Complex.Zero;
                for (int j = 0; j < delays.Length; j++)
                    hk += paths[j] * Complex.Exp(new Complex(0, -2 * Math.PI * k[i] * delays[j] / nf));
                double pw = hk.Real * hk.Real + hk.Imaginary * hk.Imaginary;
                sum += pw == 0 ? 0.5 : Metrics.QpskBerTheory(c.EbN0Db!.Value + 10 * Math.Log10(pw));
            }
            theory = sum / u;
        }
        return new QpskLinkReport(c, d0 % sps, d0 / sps, f, Wrap(Math.Atan2(hs.Imaginary, hs.Real)), Metrics.Evm(z, a),
            Metrics.BitErrors(bits, got), theory);
    }

    // |Σ_n x[d + n]·e^{−jψ_l(n)}|² over one symbol, as FskDemodNoncoherent computes it
    private static double Energy(Complex[] x, int d, int l, double[,] re, double[,] im)
    {
        double sr = 0, si = 0;
        for (int t = 0; t < re.GetLength(1); t++)
        {
            Complex v = x[d + t];
            sr += v.Real * re[l, t] - v.Imaginary * im[l, t];
            si += v.Real * im[l, t] + v.Imaginary * re[l, t];
        }
        return sr * sr + si * si;
    }

    private static void Gains(IReadOnlyList<double>? g, string name, string paramName)
    {
        if (g is null)
            return;
        if (g.Count != 2)
            throw new ArgumentException($"{name} must be null or a pair [kp, ki]", paramName);
        foreach (double x in g)
            if (!double.IsFinite(x) || x < 0)
                throw new ArgumentOutOfRangeException(paramName, x, $"{name} must be finite and at least 0");
    }

    /// <summary>Into (−π, π].</summary>
    private static double Wrap(double phi)
    {
        phi = Math.IEEERemainder(phi, 2 * Math.PI);
        return phi <= -Math.PI ? Math.PI : phi;
    }
}
