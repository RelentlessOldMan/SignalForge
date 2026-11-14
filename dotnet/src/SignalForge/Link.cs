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
        var tx = new Complex[c.DelaySamples + shaped.Length];
        shaped.CopyTo(tx, c.DelaySamples);
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
        if (c.CarrierLoopGains is { } cg)
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
        double? theory = c.EbN0Db is not { } eb ? null : mod switch
        {
            1 => Metrics.Qam16BerTheory(eb),
            2 => Metrics.Psk8BerTheory(eb),
            3 => Metrics.Qam64BerTheory(eb),
            _ => Metrics.QpskBerTheory(eb),
        };
        return new QpskLinkReport(c, tau, k0, f, phi, Metrics.Evm(z, a), Metrics.BitErrors(bits, got), theory);
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

    // the OFDM link (conventions: QPSK link, OFDM; ADR 0063)
    private static QpskLinkReport OfdmLink(QpskLinkConfig c, int[] k)
    {
        int nf = c.OfdmNfft, cp = c.OfdmCpLen, sps = c.SamplesPerSymbol, u = k.Length;
        double fs = c.SymbolRate * sps;
        if (c.NumSymbols % u != 0 || c.PreambleSymbols % u != 0)
            throw new ArgumentException($"NumSymbols and PreambleSymbols must be multiples of {u} (subcarriers)", nameof(c));
        Dsp.RrcTaps(c.Rolloff, sps, c.SpanSymbols); // checked as for the other modulations
        if (c.TimingLoopGains is not null || c.CarrierLoopGains is not null)
            throw new ArgumentException("ofdm takes no TimingLoopGains or CarrierLoopGains", nameof(c));
        if (c.PhaseNoiseLinewidthHz != 0 || c.ClockOffsetPpm != 0)
            throw new ArgumentException("ofdm takes no phase noise or clock offset", nameof(c));
        if (!(Math.Abs(c.FrequencyOffsetHz) < fs / (2 * nf)))
            throw new ArgumentOutOfRangeException(nameof(c), c.FrequencyOffsetHz, "ofdm needs |FrequencyOffsetHz| below half a subcarrier spacing");
        int b = c.NumSymbols / u, p = c.PreambleSymbols / u;
        byte[] bits = Waveforms.Prbs(c.PrbsOrder, 2 * c.NumSymbols);
        Complex[] a = SignalForge.Modulation.QpskMap(bits);
        Complex[] frame = SignalForge.Modulation.OfdmModulate(a, nf, cp, k);
        var tx = new Complex[c.DelaySamples + frame.Length];
        frame.CopyTo(tx, c.DelaySamples);
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
        // 2. derotate and demodulate; 3. channel from the preamble blocks
        Complex[] y = Channel.FrequencyOffset(rx.AsSpan(d0, length), -f, fs);
        Complex[] zm = SignalForge.Modulation.OfdmDemodulate(y, nf, cp, k);
        var h = new Complex[u];
        for (int j = 0; j < p; j++)
            for (int i = 0; i < u; i++)
                h[i] += zm[j * u + i] / a[j * u + i];
        for (int i = 0; i < u; i++)
            h[i] /= p;
        // 4. equalize, then the common phase per block, decision-directed
        var z = new Complex[zm.Length];
        var w = new Complex[u];
        double theta = 0;
        for (int j = 0; j < b; j++)
        {
            var back = new Complex(Math.Cos(theta), -Math.Sin(theta));
            for (int i = 0; i < u; i++)
                w[i] = zm[j * u + i] / h[i] * back;
            Complex[] q = SignalForge.Modulation.QpskMap(SignalForge.Modulation.QpskDemapHard(w));
            Complex s = Complex.Zero;
            for (int i = 0; i < u; i++)
                s += zm[j * u + i] / h[i] * Complex.Conjugate(q[i]);
            theta = Math.Atan2(s.Imaginary, s.Real);
            back = new Complex(Math.Cos(theta), -Math.Sin(theta));
            for (int i = 0; i < u; i++)
                z[j * u + i] = zm[j * u + i] / h[i] * back;
        }
        Complex hs = Complex.Zero;
        foreach (Complex v in h)
            hs += v;
        byte[] got = SignalForge.Modulation.QpskDemapHard(z);
        double? theory = c.EbN0Db is { } eb ? Metrics.QpskBerTheory(eb) : null;
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
