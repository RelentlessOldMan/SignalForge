using System.Numerics;

namespace SignalForge;

/// <summary>Convolution, upsampling, root-raised-cosine pulse shaping, FIR and IIR design and
/// response, resampling. Definitions in docs/conventions.md (Pulse shaping, FIR filters, IIR
/// filters, Resampling).</summary>
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

    /// <summary>Default anti-aliasing taps for <see cref="Resample(ReadOnlySpan{double}, int, int, double[])"/>:
    /// FirLowpass(20R + 1, 1/(2R), 1) with R = max(up, down) after reducing by their gcd
    /// (conventions: Resampling).</summary>
    /// <param name="up">Interpolation factor, at least 1.</param>
    /// <param name="down">Decimation factor, at least 1.</param>
    public static double[] ResampleTaps(int up, int down)
    {
        var (l, m) = Factors(up, down);
        int r = Math.Max(l, m);
        if (r == 1)
            throw new ArgumentException("up and down reduce to 1/1, which needs no filter", nameof(up));
        return FirLowpass(checked(20 * r + 1), 1.0 / (2 * r), 1);
    }

    /// <summary>Resamples by up/down with the filter delay removed: output m is at input time
    /// m·down/up (conventions: Resampling).</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="up">Interpolation factor, at least 1.</param>
    /// <param name="down">Decimation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length with unit DC gain; null for <see cref="ResampleTaps"/>.</param>
    public static double[] Resample(ReadOnlySpan<double> x, int up, int down, double[]? taps = null) =>
        ResampleCore(x, up, down, taps, static (s, v, h) => s + v * h);

    /// <summary>Complex form of <see cref="Resample(ReadOnlySpan{double}, int, int, double[])"/>.</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="up">Interpolation factor, at least 1.</param>
    /// <param name="down">Decimation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length with unit DC gain; null for <see cref="ResampleTaps"/>.</param>
    public static Complex[] Resample(ReadOnlySpan<Complex> x, int up, int down, double[]? taps = null) =>
        ResampleCore(x, up, down, taps, static (s, v, h) => s + v * h);

    /// <summary>Resample(x, factor, 1, taps).</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="factor">Interpolation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length; null for the default.</param>
    public static double[] Interpolate(ReadOnlySpan<double> x, int factor, double[]? taps = null) => Resample(x, factor, 1, taps);

    /// <summary>Resample(x, factor, 1, taps).</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="factor">Interpolation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length; null for the default.</param>
    public static Complex[] Interpolate(ReadOnlySpan<Complex> x, int factor, double[]? taps = null) => Resample(x, factor, 1, taps);

    /// <summary>Resample(x, 1, factor, taps).</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="factor">Decimation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length; null for the default.</param>
    public static double[] Decimate(ReadOnlySpan<double> x, int factor, double[]? taps = null) => Resample(x, 1, factor, taps);

    /// <summary>Resample(x, 1, factor, taps).</summary>
    /// <param name="x">Samples, non-empty.</param>
    /// <param name="factor">Decimation factor, at least 1.</param>
    /// <param name="taps">Real taps of odd length; null for the default.</param>
    public static Complex[] Decimate(ReadOnlySpan<Complex> x, int factor, double[]? taps = null) => Resample(x, 1, factor, taps);

    private static T[] ResampleCore<T>(ReadOnlySpan<T> x, int up, int down, double[]? taps, Func<T, T, double, T> mac)
        where T : struct
    {
        if (x.IsEmpty)
            throw new ArgumentException("x must be non-empty", nameof(x));
        var (l, m) = Factors(up, down);
        double[] h;
        if (taps is null)
        {
            if (l == 1 && m == 1)
                return x.ToArray();
            h = ResampleTaps(l, m);
        }
        else
        {
            CheckTaps(taps);
            if (taps.Length % 2 == 0)
                throw new ArgumentException("resample needs an odd number of taps", nameof(taps));
            h = taps;
        }
        int d = (h.Length - 1) / 2;
        long nOut = (checked((long)x.Length * l) + m - 1) / m;
        var y = new T[checked((int)nOut)];
        for (int i = 0; i < y.Length; i++)
        {
            long n0 = (long)i * m + d; // index into the zero-stuffed signal
            T s = default;
            // only taps k with n0 − k a multiple of l meet a real sample x[(n0 − k)/l]
            for (long k = n0 % l; k < h.Length && k <= n0; k += l)
            {
                long j = (n0 - k) / l;
                if (j < x.Length)
                    s = mac(s, x[(int)j], h[k]);
            }
            y[i] = mac(default, s, l);
        }
        return y;
    }

    private static (int L, int M) Factors(int up, int down)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(up, 1);
        ArgumentOutOfRangeException.ThrowIfLessThan(down, 1);
        int a = up, b = down;
        while (b != 0)
            (a, b) = (b, a % b);
        return (up / a, down / a);
    }

    /// <summary>Butterworth low-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="cutoff">−3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] ButterworthLowpass(int order, double cutoff, double sampleRate) =>
        Butterworth(order, cutoff, sampleRate, false);

    /// <summary>Butterworth high-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="cutoff">−3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] ButterworthHighpass(int order, double cutoff, double sampleRate) =>
        Butterworth(order, cutoff, sampleRate, true);

    /// <summary>Butterworth band-pass from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>
    /// (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, at least 1; the filter's order is twice it.</param>
    /// <param name="low">Lower −3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper −3 dB frequency in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] ButterworthBandpass(int order, double low, double high, double sampleRate) =>
        ButterworthBand(order, low, high, sampleRate, false);

    /// <summary>Butterworth band-stop from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>
    /// (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, at least 1; the filter's order is twice it.</param>
    /// <param name="low">Lower −3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper −3 dB frequency in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] ButterworthBandstop(int order, double low, double high, double sampleRate) =>
        ButterworthBand(order, low, high, sampleRate, true);

    /// <summary>Complex response of a cascade of second-order sections at each frequency
    /// (conventions: IIR filters).</summary>
    /// <param name="sos">Sections <c>[b0, b1, b2, a0, a1, a2]</c>, at least one, finite, a0 ≠ 0.</param>
    /// <param name="frequencies">Frequencies in Hz, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static Complex[] SosResponse(double[][] sos, ReadOnlySpan<double> frequencies, double sampleRate)
    {
        double[][] s = CheckSos(sos);
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        var h = new Complex[frequencies.Length];
        for (int i = 0; i < frequencies.Length; i++)
        {
            if (!double.IsFinite(frequencies[i]))
                throw new ArgumentException("frequencies must be finite", nameof(frequencies));
            Complex zi = Complex.FromPolarCoordinates(1, -2 * Math.PI * frequencies[i] / fs);
            Complex r = Complex.One;
            foreach (double[] c in s)
                r *= (c[0] + zi * (c[1] + zi * c[2])) / (c[3] + zi * (c[4] + zi * c[5]));
            h[i] = r;
        }
        return h;
    }

    /// <summary>A copy of the sections, each row divided by its a0; throws unless valid.</summary>
    internal static double[][] CheckSos(double[][] sos)
    {
        ArgumentNullException.ThrowIfNull(sos);
        if (sos.Length == 0)
            throw new ArgumentException("sos needs at least one section", nameof(sos));
        var s = new double[sos.Length][];
        for (int i = 0; i < sos.Length; i++)
        {
            double[] row = sos[i];
            if (row is null || row.Length != 6)
                throw new ArgumentException("every section needs 6 values [b0, b1, b2, a0, a1, a2]", nameof(sos));
            if (!Array.TrueForAll(row, double.IsFinite))
                throw new ArgumentException("sos must be finite", nameof(sos));
            if (row[3] == 0)
                throw new ArgumentException("every section needs a0 != 0", nameof(sos));
            s[i] = [.. row.Select(v => v / row[3])];
        }
        return s;
    }

    /// <summary>Chebyshev type I low-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="rippleDb">Pass-band ripple in dB, in (0, 200].</param>
    /// <param name="cutoff">Pass-band edge in Hz (where the response is −rippleDb), between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev1Lowpass(int order, double rippleDb, double cutoff, double sampleRate) =>
        Chebyshev1(order, rippleDb, cutoff, sampleRate, false);

    /// <summary>Chebyshev type I high-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="rippleDb">Pass-band ripple in dB, in (0, 200].</param>
    /// <param name="cutoff">Pass-band edge in Hz (where the response is −rippleDb), between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev1Highpass(int order, double rippleDb, double cutoff, double sampleRate) =>
        Chebyshev1(order, rippleDb, cutoff, sampleRate, true);

    /// <summary>Chebyshev type II low-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="attenuationDb">Stop-band attenuation in dB, in (0, 200].</param>
    /// <param name="cutoff">Stop-band edge in Hz (where the response first reaches −attenuationDb), between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev2Lowpass(int order, double attenuationDb, double cutoff, double sampleRate) =>
        Chebyshev2(order, attenuationDb, cutoff, sampleRate, false);

    /// <summary>Chebyshev type II high-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, at least 1.</param>
    /// <param name="attenuationDb">Stop-band attenuation in dB, in (0, 200].</param>
    /// <param name="cutoff">Stop-band edge in Hz (where the response first reaches −attenuationDb), between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev2Highpass(int order, double attenuationDb, double cutoff, double sampleRate) =>
        Chebyshev2(order, attenuationDb, cutoff, sampleRate, true);

    /// <summary>Chebyshev type I band-pass from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>:
    /// pass band [low, high] rippling by rippleDb (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 1000; the filter's order is twice it.</param>
    /// <param name="rippleDb">Pass-band ripple in dB, in (0, 200].</param>
    /// <param name="low">Lower pass-band edge in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper pass-band edge in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev1Bandpass(int order, double rippleDb, double low, double high, double sampleRate) =>
        Chebyshev1Band(order, rippleDb, low, high, sampleRate, false);

    /// <summary>Chebyshev type I band-stop from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>:
    /// pass bands up to low and from high, rippling by rippleDb (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 1000; the filter's order is twice it.</param>
    /// <param name="rippleDb">Pass-band ripple in dB, in (0, 200].</param>
    /// <param name="low">Lower pass-band edge in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper pass-band edge in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev1Bandstop(int order, double rippleDb, double low, double high, double sampleRate) =>
        Chebyshev1Band(order, rippleDb, low, high, sampleRate, true);

    /// <summary>Chebyshev type II band-pass from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>:
    /// stop bands up to low and from high, peaks at −attenuationDb (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 1000; the filter's order is twice it.</param>
    /// <param name="attenuationDb">Stop-band attenuation in dB, in (0, 200].</param>
    /// <param name="low">Lower stop-band edge in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper stop-band edge in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev2Bandpass(int order, double attenuationDb, double low, double high, double sampleRate) =>
        Chebyshev2Band(order, attenuationDb, low, high, sampleRate, false);

    /// <summary>Chebyshev type II band-stop from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>:
    /// stop band [low, high], peaks at −attenuationDb (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 1000; the filter's order is twice it.</param>
    /// <param name="attenuationDb">Stop-band attenuation in dB, in (0, 200].</param>
    /// <param name="low">Lower stop-band edge in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper stop-band edge in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] Chebyshev2Bandstop(int order, double attenuationDb, double low, double high, double sampleRate) =>
        Chebyshev2Band(order, attenuationDb, low, high, sampleRate, true);

    private static double Theta(int i, int n) => Math.PI / 2 + Math.PI * (2 * i + 1) / (2.0 * n);

    private static double[][] Butterworth(int order, double cutoff, double sampleRate, bool high)
    {
        Order(order);
        return Cascade(order, cutoff, sampleRate, high, i => Complex.FromPolarCoordinates(1, Theta(i, order)));
    }

    private static double[][] Chebyshev1(int order, double rippleDb, double cutoff, double sampleRate, bool high)
    {
        Order(order);
        double mu = Math.Asinh(1 / Math.Sqrt(DbPowerRatio(rippleDb, nameof(rippleDb)))) / order;
        double sh = Math.Sinh(mu), ch = Math.Cosh(mu);
        double[][] rows = Cascade(order, cutoff, sampleRate, high, i => new Complex(sh * Math.Cos(Theta(i, order)), ch * Math.Sin(Theta(i, order))));
        if (order % 2 == 0)
        {
            double g = Math.Pow(10, -rippleDb / 20); // the ripple's low point at DC (or fs/2)
            for (int j = 0; j < 3; j++)
                rows[0][j] *= g;
        }
        return rows;
    }

    private static double[][] Chebyshev2(int order, double attenuationDb, double cutoff, double sampleRate, bool high)
    {
        Order(order);
        double mu = Math.Asinh(Math.Sqrt(DbPowerRatio(attenuationDb, nameof(attenuationDb)))) / order;
        double sh = Math.Sinh(mu), ch = Math.Cosh(mu);
        return Cascade(order, cutoff, sampleRate, high,
            i => 1 / new Complex(sh * Math.Cos(Theta(i, order)), ch * Math.Sin(Theta(i, order))),
            i => 1 / Math.Sin(Theta(i, order)));
    }

    // 10^(x/10) − 1 for 0 < x ≤ 200 dB, without losing digits for small x.
    private static double DbPowerRatio(double x, string name)
    {
        if (!(Check.Finite(x, name) > 0 && x <= 200))
            throw new ArgumentOutOfRangeException(name, x, "must be in (0, 200] dB");
        double y = x * Math.Log(10) / 10; // expm1(y), which .NET lacks: Exp(y) − 1 loses digits for small y
        return y < 1e-5 ? y + y * y / 2 + y * y * y / 6 : Math.Exp(y) - 1;
    }

    private static void Order(int order)
    {
        if (order is < 1 or > 1000)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be between 1 and 1000");
    }

    // The design's sections, if each is finite and strictly stable; a cutoff (or band edge) too near
    // 0 or fs/2 rounds to a pole on the unit circle and is rejected.
    private static double[][] Usable(List<double[]> rows)
    {
        foreach (double[] r in rows)
            if (!(Array.TrueForAll(r, double.IsFinite) && Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5]))
                throw new ArgumentException("the design rounds to a pole on or outside the unit circle: the cutoff is too "
                    + "close to 0 or sampleRate/2 (or the dB value too small) for double precision");
        return [.. rows];
    }

    // Sections from the analog prototype poles (cutoff 1) and, for pair i, zeros at s = ±j·zeros(i)
    // (default: Butterworth's, at infinity): low-pass or high-pass, prewarped bilinear transform,
    // Butterworth section order and unit gain at DC or fs/2.
    private static double[][] Cascade(int order, double cutoff, double sampleRate, bool high, Func<int, Complex> prototype,
        Func<int, double>? zeros = null)
    {
        double k = Math.Tan(Math.PI * BandEdge(cutoff, Check.PositiveFinite(sampleRate, nameof(sampleRate)), nameof(cutoff)));
        double zero = high ? 1 : -1; // zeros at z = 1 (high-pass) or z = -1 (low-pass)

        // Prototype pole i scaled to the prewarped cutoff, through the bilinear transform.
        Complex Pole(int i)
        {
            Complex s = high ? k / prototype(i) : k * prototype(i);
            return (1 + s) / (1 - s);
        }

        var rows = new List<double[]>();
        if (order % 2 == 1)
        {
            double p = Pole((order - 1) / 2).Real;
            double g = high ? (1 + p) / 2 : (1 - p) / 2; // unit gain at fs/2 or DC
            rows.Add([g, -zero * g, 0, 1, -p, 0]);
        }
        for (int i = order / 2 - 1; i >= 0; i--)
        {
            Complex z = Pole(i);
            double a1 = -2 * z.Real, a2 = z.Magnitude * z.Magnitude;
            // Numerator 1 − 2c z⁻¹ + z⁻²: a double zero at z = zero, or a pair on the circle; reference =
            // 2 + 2·zero·c, its value at z = −zero, exactly.
            double c = zero, reference = 4;
            if (zeros is not null)
            {
                double w = high ? k / zeros(i) : k * zeros(i);
                c = (1 - w * w) / (1 + w * w);
                reference = high ? 4 / (1 + w * w) : 4 * w * w / (1 + w * w);
            }
            double g = (1 - zero * a1 + a2) / reference; // unit gain at the reference z = -zero
            rows.Add([g, -2 * c * g, g, 1, a1, a2]);
        }
        return Usable(rows);
    }

    private static double[][] ButterworthBand(int order, double low, double high, double sampleRate, bool stop)
    {
        Order(order);
        return Band(order, low, high, sampleRate, stop, i => Complex.FromPolarCoordinates(1, Theta(i, order)), unit: true);
    }

    // Type I prototype poles for ripple db (inverse: type II, their reciprocals, for attenuation db).
    private static Func<int, Complex> ChebyshevPoles(int n, double db, string name, bool inverse)
    {
        double eps2 = DbPowerRatio(db, name);
        double mu = Math.Asinh(inverse ? Math.Sqrt(eps2) : 1 / Math.Sqrt(eps2)) / n;
        double sh = Math.Sinh(mu), ch = Math.Cosh(mu);
        return i =>
        {
            var p = new Complex(sh * Math.Cos(Theta(i, n)), ch * Math.Sin(Theta(i, n)));
            return inverse ? 1 / p : p;
        };
    }

    private static double[][] Chebyshev1Band(int order, double rippleDb, double low, double high, double sampleRate, bool stop)
    {
        Order(order);
        double[][] rows = Band(order, low, high, sampleRate, stop, ChebyshevPoles(order, rippleDb, nameof(rippleDb), false));
        if (order % 2 == 0)
        {
            double g = Math.Pow(10, -rippleDb / 20); // the ripple's low point at the reference
            for (int j = 0; j < 3; j++)
                rows[0][j] *= g;
        }
        return rows;
    }

    private static double[][] Chebyshev2Band(int order, double attenuationDb, double low, double high, double sampleRate, bool stop)
    {
        Order(order);
        return Band(order, low, high, sampleRate, stop, ChebyshevPoles(order, attenuationDb, nameof(attenuationDb), true),
            i => 1 / Math.Sin(Theta(i, order)));
    }

    // Band-pass or band-stop sections from the low-pass prototype's poles (edge 1) and, for pair i,
    // zeros at s = ±j·zeros(i) (default: at infinity), with the prototype's gain (unit: the poles are
    // on the unit circle, so the pair gains are exactly 1).
    private static double[][] Band(int order, double low, double high, double sampleRate, bool stop,
        Func<int, Complex> prototype, Func<int, double>? zeros = null, bool unit = false)
    {
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        double lo = Math.Tan(Math.PI * BandEdge(low, fs, nameof(low)));
        double hi = Math.Tan(Math.PI * BandEdge(high, fs, nameof(high)));
        if (lo >= hi)
            throw new ArgumentException("low must be below high", nameof(low));
        double w2 = lo * hi, bw = hi - lo; // center squared and width, prewarped
        var rows = new List<double[]>();

        // Analog section with poles at s and its conjugate (sigma = Re s, m = |s|²) times gain, through
        // the bilinear transform s = (1 − z⁻¹)/(1 + z⁻¹), divided by a0; numerator s² + zero2 if
        // given, else as for Butterworth.
        void Section(double sigma, double m, double gain, double? zero2)
        {
            double a0 = 1 - 2 * sigma + m;
            double[] b = zero2 is { } z2 ? [1 + z2, 2 * (z2 - 1), 1 + z2] // (s² + zero2) / ...
                : stop ? [1 + w2, 2 * (w2 - 1), 1 + w2] // (s² + w2) / ...
                : [bw, 0, -bw]; // bw·s / ...
            rows.Add([gain * b[0] / a0, gain * b[1] / a0, gain * b[2] / a0, 1, 2 * (m - 1) / a0, (1 + 2 * sigma + m) / a0]);
        }

        if (order % 2 == 1) // the real pole p maps to s² − c·s + w2, one section whatever its roots
        {
            double p = prototype((order - 1) / 2).Real;
            double c = stop ? bw / p : bw * p;
            Section(c / 2, w2, stop ? 1 : -p, null);
        }
        for (int i = order / 2 - 1; i >= 0; i--)
        {
            Complex p = prototype(i);
            Complex c = stop ? bw / p : bw * p; // the pole's two images: roots of s² − c·s + w2
            Complex r = Complex.Sqrt(c * c - 4 * w2);
            Complex s1 = (c + r) / 2, s2 = (c - r) / 2;
            if (s2.Magnitude < s1.Magnitude)
                (s1, s2) = (s2, s1);
            double gain = stop || unit ? 1 : p.Magnitude;
            double? z1 = null, z2 = null;
            if (zeros is not null) // j·omega maps to j·wHi and j·wLo, wHi·wLo = w2
            {
                double d = stop ? bw / zeros(i) : bw * zeros(i);
                double wHi = (d + Math.Sqrt(d * d + 4 * w2)) / 2, wLo = w2 / wHi;
                gain = stop ? 1 : p.Magnitude / zeros(i);
                (z1, z2) = (wLo * wLo, wHi * wHi);
            }
            Section(s1.Real, s1.Magnitude * s1.Magnitude, gain, z1);
            Section(s2.Real, s2.Magnitude * s2.Magnitude, gain, z2);
        }
        return Usable(rows);
    }

    /// <summary>The sections run forward, then backward, over the samples extended by
    /// <paramref name="pad"/> samples of odd reflection at each end, each pass starting in its
    /// steady state; zero phase, magnitude |H|² (conventions: IIR filters).</summary>
    /// <param name="sos">Sections <c>[b0, b1, b2, a0, a1, a2]</c>, none with a pole at z = 1.</param>
    /// <param name="samples">Real samples, more than <paramref name="pad"/>.</param>
    /// <param name="pad">Samples of extension at each end; default 3·(2·sections + 1).</param>
    public static double[] ZeroPhaseFilter(double[][] sos, ReadOnlySpan<double> samples, int? pad = null)
    {
        var (s, p) = ZeroPhaseCheck(sos, samples.Length, pad);
        foreach (double v in samples)
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite: one non-finite sample spoils every output", nameof(samples));
        double[] y = new double[samples.Length + 2 * p];
        for (int i = 0; i < p; i++)
        {
            y[i] = 2 * samples[0] - samples[p - i];
            y[p + samples.Length + i] = 2 * samples[^1] - samples[samples.Length - 2 - i];
        }
        samples.CopyTo(y.AsSpan(p));
        SteadyPass(s, y);
        Array.Reverse(y);
        SteadyPass(s, y);
        Array.Reverse(y);
        return y[p..(p + samples.Length)];
    }

    /// <summary>The sections run forward, then backward, over complex samples; otherwise as for
    /// real samples.</summary>
    /// <param name="sos">Sections <c>[b0, b1, b2, a0, a1, a2]</c>, none with a pole at z = 1.</param>
    /// <param name="samples">Complex samples, more than <paramref name="pad"/>.</param>
    /// <param name="pad">Samples of extension at each end; default 3·(2·sections + 1).</param>
    public static Complex[] ZeroPhaseFilter(double[][] sos, ReadOnlySpan<Complex> samples, int? pad = null)
    {
        var (s, p) = ZeroPhaseCheck(sos, samples.Length, pad);
        foreach (Complex v in samples)
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite: one non-finite sample spoils every output", nameof(samples));
        Complex[] y = new Complex[samples.Length + 2 * p];
        for (int i = 0; i < p; i++)
        {
            y[i] = 2 * samples[0] - samples[p - i];
            y[p + samples.Length + i] = 2 * samples[^1] - samples[samples.Length - 2 - i];
        }
        samples.CopyTo(y.AsSpan(p));
        SteadyPass(s, y);
        Array.Reverse(y);
        SteadyPass(s, y);
        Array.Reverse(y);
        return y[p..(p + samples.Length)];
    }

    private static (double[][] Sos, int Pad) ZeroPhaseCheck(double[][] sos, int length, int? pad)
    {
        double[][] s = CheckSos(sos);
        if (Array.Exists(s, r => 1 + r[4] + r[5] == 0))
            throw new ArgumentException("every section needs 1 + a1 + a2 != 0 (no pole at z = 1)", nameof(sos));
        int p = pad ?? 3 * (2 * s.Length + 1);
        ArgumentOutOfRangeException.ThrowIfNegative(p, nameof(pad));
        if (length <= p)
            throw new ArgumentException("samples must be longer than pad", nameof(pad));
        if (length + 2L * p > Array.MaxLength)
            throw new ArgumentException("samples plus twice pad must fit in one array", nameof(pad));
        return (s, p);
    }

    // Each section starts in its steady state for a constant input equal to the first sample it sees.
    private static void SteadyPass(double[][] sos, double[] y)
    {
        double u = y[0];
        foreach (double[] c in sos)
        {
            double g = (c[0] + c[1] + c[2]) / (1 + c[4] + c[5]);
            double s2 = (c[2] - c[5] * g) * u; // transposed direct form II, as if u had always been the input
            double s1 = (c[1] - c[4] * g) * u + s2;
            for (int i = 0; i < y.Length; i++)
            {
                double v = y[i], o = c[0] * v + s1;
                s1 = c[1] * v - c[4] * o + s2;
                s2 = c[2] * v - c[5] * o;
                y[i] = o;
            }
            u = g * u;
        }
    }

    private static void SteadyPass(double[][] sos, Complex[] y)
    {
        Complex u = y[0];
        foreach (double[] c in sos)
        {
            double g = (c[0] + c[1] + c[2]) / (1 + c[4] + c[5]);
            Complex s2 = (c[2] - c[5] * g) * u;
            Complex s1 = (c[1] - c[4] * g) * u + s2;
            for (int i = 0; i < y.Length; i++)
            {
                Complex v = y[i], o = c[0] * v + s1;
                s1 = c[1] * v - c[4] * o + s2;
                s2 = c[2] * v - c[5] * o;
                y[i] = o;
            }
            u = g * u;
        }
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
