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
}

/// <summary>What the receiver estimated and measured on one link run.</summary>
/// <param name="Config">The run's configuration.</param>
/// <param name="TimingOffset">Symbol timing estimate in samples, in [0, sps).</param>
/// <param name="FrameStart">Frame start in symbols into the sampled stream.</param>
/// <param name="FrequencyOffsetHz">Carrier frequency estimate in Hz.</param>
/// <param name="PhaseOffset">Carrier phase at the frame's first symbol in radians, in (−π, π].</param>
/// <param name="Evm">EVM of the recovered symbols.</param>
/// <param name="BitErrors">Bit errors over the frame, preamble included.</param>
/// <param name="BerTheory">Theoretical BER at the configured Eb/N0; null without noise.</param>
public sealed record QpskLinkReport(
    QpskLinkConfig Config,
    double TimingOffset,
    int FrameStart,
    double FrequencyOffsetHz,
    double PhaseOffset,
    Evm Evm,
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

/// <summary>End-to-end QPSK link: bits, shaping, channel, recovery, EVM and BER.</summary>
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
        if (!(c.PhaseNoiseLinewidthHz >= 0) || !double.IsFinite(c.PhaseNoiseLinewidthHz))
            throw new ArgumentOutOfRangeException(nameof(config), c.PhaseNoiseLinewidthHz, "PhaseNoiseLinewidthHz must be finite and at least 0");
        if (!(Math.Abs(c.ClockOffsetPpm) <= 1e5))
            throw new ArgumentOutOfRangeException(nameof(config), c.ClockOffsetPpm, "ClockOffsetPpm must be finite and within 1e5");
        Gains(c.TimingLoopGains, nameof(c.TimingLoopGains), nameof(config));
        Gains(c.CarrierLoopGains, nameof(c.CarrierLoopGains), nameof(config));

        // transmitter
        byte[] bits = Waveforms.Prbs(c.PrbsOrder, 2 * n);
        Complex[] a = Modulation.QpskMap(bits);
        double[] h = Dsp.RrcTaps(c.Rolloff, sps, c.SpanSymbols);
        Complex[] shaped = Dsp.PulseShape(a, h, sps);
        var tx = new Complex[c.DelaySamples + shaped.Length];
        shaped.CopyTo(tx, c.DelaySamples);
        // channel
        Complex[] rx = Channel.FrequencyOffset(tx, c.FrequencyOffsetHz, rs * sps, c.Phase);
        var rng = new Random(c.Seed);
        if (c.PhaseNoiseLinewidthHz > 0)
            rx = Channel.PhaseNoise(rx, c.PhaseNoiseLinewidthHz, rs * sps, rng);
        if (c.ClockOffsetPpm != 0)
            rx = Channel.ClockOffset(rx, c.ClockOffsetPpm);
        if (c.EbN0Db is { } ebN0Db)
            rx = Channel.Awgn(rx, ebN0Db + 10 * Math.Log10(2), sps, rng, signalPower: 1.0 / sps);
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
        double f = Sync.QpskFrequencyOffset(r, rs);
        // frame start: the first maximum of the preamble correlation
        Complex[] cr = Channel.FrequencyOffset(r, -f, rs);
        int k0 = 0;
        double best = -1;
        for (int k = 0; k <= cr.Length - n; k++)
        {
            Complex s = Complex.Zero;
            for (int i = 0; i < pre; i++)
                s += Complex.Conjugate(a[i]) * cr[k + i];
            if (s.Magnitude > best)
                (best, k0) = (s.Magnitude, k);
        }
        // fine frequency and phase: a line through the unwrapped block phases at each block's middle
        Complex[] z = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs);
        double[] ph = Sync.QpskBlockPhases(z, blk);
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
        // the preamble resolves the π/2 ambiguity
        Complex[] zp = Channel.FrequencyOffset(z.AsSpan(0, pre), -slope * rs / (2 * Math.PI), rs, -phi);
        Complex cp = Complex.Zero;
        for (int i = 0; i < pre; i++)
            cp += Complex.Conjugate(a[i]) * zp[i];
        phi = Wrap(phi + Math.PI / 2 * Math.Round(Math.Atan2(cp.Imaginary, cp.Real) / (Math.PI / 2)));
        if (c.CarrierLoopGains is { } cg)
        {
            Complex[] w = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs);
            Complex cw = Complex.Zero;
            for (int i = 0; i < pre; i++)
                cw += Complex.Conjugate(a[i]) * w[i];
            z = Sync.QpskCarrierTracking(w, cg[0], cg[1], Math.Atan2(cw.Imaginary, cw.Real)).Symbols;
        }
        else
            z = Channel.FrequencyOffset(r.AsSpan(k0, n), -f, rs, -phi);

        return new QpskLinkReport(c, tau, k0, f, phi, Metrics.Evm(z, a), Metrics.BitErrors(bits, Modulation.QpskDemapHard(z)),
            c.EbN0Db is { } eb ? Metrics.QpskBerTheory(eb) : null);
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
