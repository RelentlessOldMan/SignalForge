using System.Numerics;

namespace SignalForge;

/// <summary>Convolution, upsampling, root-raised-cosine pulse shaping, FIR design and FIR response.
/// Definitions in docs/conventions.md (Pulse shaping, FIR filters).</summary>
public static class Dsp
{
    /// <summary>Full linear convolution y[n] = Σ h[k]·x[n−k], length len(x) + len(h) − 1.</summary>
    public static double[] Convolve(ReadOnlySpan<double> x, ReadOnlySpan<double> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new double[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Full linear convolution of complex samples with real taps.</summary>
    public static Complex[] Convolve(ReadOnlySpan<Complex> x, ReadOnlySpan<double> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new Complex[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Full linear convolution of complex samples with complex taps.</summary>
    public static Complex[] Convolve(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new Complex[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Each sample followed by <paramref name="factor"/> − 1 zeros.</summary>
    public static double[] Upsample(ReadOnlySpan<double> x, int factor)
    {
        CheckUpsample(x.Length, factor);
        var y = new double[x.Length * factor];
        for (int i = 0; i < x.Length; i++)
            y[i * factor] = x[i];
        return y;
    }

    /// <summary>Each complex sample followed by <paramref name="factor"/> − 1 zeros.</summary>
    public static Complex[] Upsample(ReadOnlySpan<Complex> x, int factor)
    {
        CheckUpsample(x.Length, factor);
        var y = new Complex[x.Length * factor];
        for (int i = 0; i < x.Length; i++)
            y[i * factor] = x[i];
        return y;
    }

    /// <summary>Root-raised-cosine taps, span·sps + 1 of them, scaled to unit energy (Σh² = 1).</summary>
    /// <param name="beta">Roll-off, 0 to 1.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="spanSymbols">Filter length in symbols, even and at least 2.</param>
    public static double[] RrcTaps(double beta, int samplesPerSymbol, int spanSymbols)
    {
        if (!(beta >= 0 && beta <= 1))
            throw new ArgumentOutOfRangeException(nameof(beta), beta, "must be in [0, 1]");
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 1);
        if (spanSymbols < 2 || spanSymbols % 2 != 0)
            throw new ArgumentOutOfRangeException(nameof(spanSymbols), spanSymbols, "must be even and at least 2");
        int n = checked(spanSymbols * samplesPerSymbol + 1);
        var h = new double[n];
        double energy = 0;
        for (int i = 0; i < n; i++)
        {
            double t = (i - (n - 1) / 2.0) / samplesPerSymbol;
            if (t == 0)
            {
                h[i] = 1 - beta + 4 * beta / Math.PI;
            }
            else if (Math.Abs(4 * beta * Math.Abs(t) - 1) < 1e-9)
            {
                double a = Math.PI / (4 * beta);
                h[i] = beta / Math.Sqrt(2) * ((1 + 2 / Math.PI) * Math.Sin(a) + (1 - 2 / Math.PI) * Math.Cos(a));
            }
            else
            {
                double num = Math.Sin(Math.PI * t * (1 - beta)) + 4 * beta * t * Math.Cos(Math.PI * t * (1 + beta));
                double q = 4 * beta * t;
                h[i] = num / (Math.PI * t * (1 - q * q));
            }
            energy += h[i] * h[i];
        }
        double scale = 1 / Math.Sqrt(energy);
        for (int i = 0; i < n; i++)
            h[i] *= scale;
        return h;
    }

    /// <summary>Convolve(Upsample(symbols, sps), taps); symbol k peaks at k·sps + (N−1)/2.</summary>
    /// <param name="symbols">Symbols, at least one.</param>
    /// <param name="taps">Shaping filter taps, at least one.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    public static Complex[] PulseShape(ReadOnlySpan<Complex> symbols, ReadOnlySpan<double> taps, int samplesPerSymbol) =>
        Convolve(Upsample(symbols, samplesPerSymbol), taps);

    /// <summary>Real-symbol form of <see cref="PulseShape(ReadOnlySpan{Complex}, ReadOnlySpan{double}, int)"/>.</summary>
    /// <param name="symbols">Symbols, at least one.</param>
    /// <param name="taps">Shaping filter taps, at least one.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    public static double[] PulseShape(ReadOnlySpan<double> symbols, ReadOnlySpan<double> taps, int samplesPerSymbol) =>
        Convolve(Upsample(symbols, samplesPerSymbol), taps);

    /// <summary>Windowed-sinc low-pass taps with unit gain at DC (conventions: FIR filters).</summary>
    /// <param name="numTaps">Number of taps, at least 1.</param>
    /// <param name="cutoff">Cutoff in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="window">Window, in its symmetric form.</param>
    /// <param name="beta">Kaiser β; only with <see cref="WindowType.Kaiser"/>.</param>
    public static double[] FirLowpass(int numTaps, double cutoff, double sampleRate,
        WindowType window = WindowType.Hamming, double? beta = null)
    {
        double nu = BandEdge(cutoff, Check.PositiveFinite(sampleRate, nameof(sampleRate)), nameof(cutoff));
        return FirDesign(numTaps, [(1.0, nu)], 0, window, beta);
    }

    /// <summary>Windowed-sinc high-pass taps with unit gain at sampleRate/2 (conventions: FIR filters).</summary>
    /// <param name="numTaps">Number of taps, odd.</param>
    /// <param name="cutoff">Cutoff in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="window">Window, in its symmetric form.</param>
    /// <param name="beta">Kaiser β; only with <see cref="WindowType.Kaiser"/>.</param>
    public static double[] FirHighpass(int numTaps, double cutoff, double sampleRate,
        WindowType window = WindowType.Hamming, double? beta = null)
    {
        double nu = BandEdge(cutoff, Check.PositiveFinite(sampleRate, nameof(sampleRate)), nameof(cutoff));
        ArgumentOutOfRangeException.ThrowIfNegative(numTaps);
        if (numTaps % 2 == 0)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "a high-pass needs an odd number of taps");
        return FirDesign(numTaps, [(1.0, 0.5), (-1.0, nu)], 0.5, window, beta);
    }

    /// <summary>Windowed-sinc band-pass taps with unit gain at the band center (low + high)/2
    /// (conventions: FIR filters).</summary>
    /// <param name="numTaps">Number of taps, at least 1.</param>
    /// <param name="low">Lower band edge in Hz, above 0.</param>
    /// <param name="high">Upper band edge in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="window">Window, in its symmetric form.</param>
    /// <param name="beta">Kaiser β; only with <see cref="WindowType.Kaiser"/>.</param>
    public static double[] FirBandpass(int numTaps, double low, double high, double sampleRate,
        WindowType window = WindowType.Hamming, double? beta = null)
    {
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        double lo = BandEdge(low, fs, nameof(low)), hi = BandEdge(high, fs, nameof(high));
        if (lo >= hi)
            throw new ArgumentException("low must be below high", nameof(low));
        return FirDesign(numTaps, [(1.0, hi), (-1.0, lo)], (lo + hi) / 2, window, beta);
    }

    /// <summary>Number of taps and Kaiser β for a Kaiser-window design, from Kaiser's formulas
    /// (conventions: FIR filters).</summary>
    /// <param name="attenuationDb">Stop-band attenuation in dB, positive.</param>
    /// <param name="transitionWidth">Transition width in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static (int NumTaps, double Beta) KaiserParameters(double attenuationDb, double transitionWidth, double sampleRate)
    {
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        double a = Check.PositiveFinite(attenuationDb, nameof(attenuationDb));
        double dw = 2 * Math.PI * BandEdge(transitionWidth, fs, nameof(transitionWidth));
        double beta = a > 50 ? 0.1102 * (a - 8.7)
            : a >= 21 ? 0.5842 * Math.Pow(a - 21, 0.4) + 0.07886 * (a - 21)
            : 0.0;
        double order = Math.Max(0, Math.Ceiling((a - 8) / (2.285 * dw)));
        if (order >= int.MaxValue)
            throw new ArgumentOutOfRangeException(nameof(transitionWidth), transitionWidth, "too narrow for any filter length");
        return ((int)order + 1, beta);
    }

    /// <summary>Complex response H(f) = Σ h[n]·e^(−j2π·f·n/fs) at each frequency.</summary>
    /// <param name="taps">Real taps, non-empty and finite.</param>
    /// <param name="frequencies">Frequencies in Hz, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static Complex[] FirResponse(ReadOnlySpan<double> taps, ReadOnlySpan<double> frequencies, double sampleRate)
    {
        CheckTaps(taps);
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        var h = new Complex[frequencies.Length];
        for (int i = 0; i < frequencies.Length; i++)
        {
            if (!double.IsFinite(frequencies[i]))
                throw new ArgumentException("frequencies must be finite", nameof(frequencies));
            Complex s = Complex.Zero;
            for (int n = 0; n < taps.Length; n++)
            {
                double ph = -2 * Math.PI * (frequencies[i] / fs) * n;
                s += taps[n] * new Complex(Math.Cos(ph), Math.Sin(ph));
            }
            h[i] = s;
        }
        return h;
    }

    /// <summary>Throws unless the taps are non-empty and finite.</summary>
    internal static void CheckTaps(ReadOnlySpan<double> taps)
    {
        if (taps.IsEmpty)
            throw new ArgumentException("taps must be non-empty", nameof(taps));
        foreach (double t in taps)
            if (!double.IsFinite(t))
                throw new ArgumentException("taps must be finite", nameof(taps));
    }

    private static double[] FirDesign(int numTaps, (double Sign, double Nu)[] ideal, double reference, WindowType window, double? beta)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(numTaps, 1);
        double[] w = Spectral.Window(window, numTaps, symmetric: true, beta);
        var h = new double[numTaps];
        double gain = 0;
        for (int n = 0; n < numTaps; n++)
        {
            double t = n - (numTaps - 1) / 2.0, d = 0;
            foreach (var (sign, nu) in ideal)
                d += sign * 2 * nu * Sinc(2 * nu * t);
            h[n] = d * w[n];
            gain += h[n] * Math.Cos(2 * Math.PI * reference * t);
        }
        if (!(Math.Abs(gain) > 1e-6 * h.Sum(Math.Abs)))
            throw new ArgumentException("too few taps: the design has almost no gain at its reference frequency", nameof(numTaps));
        for (int n = 0; n < numTaps; n++)
            h[n] /= gain;
        return h;
    }

    private static double Sinc(double x) => x == 0 ? 1 : Math.Sin(Math.PI * x) / (Math.PI * x);

    /// <summary>f/fs for a frequency strictly between 0 and fs/2.</summary>
    private static double BandEdge(double f, double fs, string name) =>
        f > 0 && f < fs / 2 ? f / fs : throw new ArgumentOutOfRangeException(name, f, "must be between 0 and sampleRate/2");

    private static void CheckNonEmpty(int nx, int nh)
    {
        if (nx == 0 || nh == 0)
            throw new ArgumentException("convolution needs non-empty inputs");
    }

    private static void CheckUpsample(int n, int factor)
    {
        if (n == 0)
            throw new ArgumentException("upsample needs at least one sample");
        ArgumentOutOfRangeException.ThrowIfLessThan(factor, 1);
        _ = checked(n * factor);
    }
}
