using System.Numerics;

namespace SignalForge;

/// <summary>Named windows. Formulas in docs/conventions.md (Spectra).</summary>
public enum WindowType
{
    /// <summary>All ones.</summary>
    Rectangular,

    /// <summary>Cosine sum 0.5, 0.5.</summary>
    Hann,

    /// <summary>Cosine sum 0.54, 0.46.</summary>
    Hamming,

    /// <summary>Cosine sum 0.42, 0.5, 0.08.</summary>
    Blackman,

    /// <summary>Four-term Blackman-Harris: 0.35875, 0.48829, 0.14128, 0.01168.</summary>
    BlackmanHarris,

    /// <summary>Five-term flat-top: 0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368.</summary>
    Flattop,

    /// <summary>Kaiser window; needs a shape parameter β ≥ 0.</summary>
    Kaiser,
}

/// <summary>Coherent gain Σw/N and equivalent noise bandwidth in bins N·Σw²/(Σw)² of a window.</summary>
/// <param name="CoherentGain">Σw / N: the reading of a unit tone at a bin center.</param>
/// <param name="EnbwBins">N·Σw² / (Σw)²: the noise bandwidth in bins.</param>
public sealed record WindowStats(double CoherentGain, double EnbwBins);

/// <summary>A power spectral density in sample-units²/Hz; see docs/conventions.md (Spectra).</summary>
/// <param name="Frequencies">Bin frequencies in Hz, ascending.</param>
/// <param name="Psd">Density at each bin, in sample-units²/Hz.</param>
/// <param name="SampleRate">Sample rate in Hz.</param>
/// <param name="Nperseg">Segment (FFT) length.</param>
/// <param name="NumSegments">Number of segments averaged.</param>
/// <param name="OneSided">True for a one-sided PSD of real input.</param>
/// <param name="BinWidth">fs / nperseg, in Hz.</param>
/// <param name="EnbwHz">The window's equivalent noise bandwidth in Hz (resolution bandwidth).</param>
public sealed record SpectralDensity(
    double[] Frequencies,
    double[] Psd,
    double SampleRate,
    int Nperseg,
    int NumSegments,
    bool OneSided,
    double BinWidth,
    double EnbwHz);

/// <summary>Occupied bandwidth by the β/2 method, in the PSD's frequency axis.</summary>
/// <param name="Bandwidth">Upper minus lower, in Hz.</param>
/// <param name="Lower">Lower band edge in Hz.</param>
/// <param name="Upper">Upper band edge in Hz.</param>
/// <param name="TotalPower">Total power of the PSD, in sample-units².</param>
/// <param name="Fraction">Fraction of the power inside the band.</param>
public sealed record OccupiedBandwidth(double Bandwidth, double Lower, double Upper, double TotalPower, double Fraction);

/// <summary>
/// FFT, frequency axes, windows, Welch PSD, occupied bandwidth and channel power. Definitions in
/// docs/conventions.md (Spectra) and docs/adr/0006-fft-windows-spectra.md.
/// </summary>
public static class Spectral
{
    private static readonly Dictionary<WindowType, double[]> CosineSums = new()
    {
        [WindowType.Rectangular] = [1.0],
        [WindowType.Hann] = [0.5, 0.5],
        [WindowType.Hamming] = [0.54, 0.46],
        [WindowType.Blackman] = [0.42, 0.5, 0.08],
        [WindowType.BlackmanHarris] = [0.35875, 0.48829, 0.14128, 0.01168],
        [WindowType.Flattop] = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368],
    };

    /// <summary>Forward DFT, unnormalized: X[k] = Σ x[n]·e^{−j2πkn/N}. Any length N ≥ 1.</summary>
    public static Complex[] Fft(ReadOnlySpan<Complex> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("fft needs at least one sample", nameof(samples));
        var x = samples.ToArray();
        Transform(x);
        return x;
    }

    /// <summary>Forward DFT of real samples; see <see cref="Fft(ReadOnlySpan{Complex})"/>.</summary>
    public static Complex[] Fft(ReadOnlySpan<double> samples) => Fft(ToComplex(samples));

    /// <summary>Inverse DFT, scaled by 1/N. Any length N ≥ 1.</summary>
    public static Complex[] Ifft(ReadOnlySpan<Complex> spectrum)
    {
        if (spectrum.IsEmpty)
            throw new ArgumentException("ifft needs at least one bin", nameof(spectrum));
        var x = new Complex[spectrum.Length];
        for (int i = 0; i < x.Length; i++)
            x[i] = Complex.Conjugate(spectrum[i]);
        Transform(x);
        double scale = 1.0 / x.Length;
        for (int i = 0; i < x.Length; i++)
            x[i] = Complex.Conjugate(x[i]) * scale;
        return x;
    }

    /// <summary>
    /// Bin frequencies of an n-point FFT: unshifted (NumPy fftfreq order) or shifted (fftshift order,
    /// ascending from −fs/2).
    /// </summary>
    public static double[] FftFrequencies(int n, double sampleRate, bool shifted = false)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(n);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(sampleRate);
        var f = new double[n];
        double df = sampleRate / n;
        for (int i = 0; i < n; i++)
        {
            int k = shifted ? i - n / 2 : (i <= (n - 1) / 2 ? i : i - n);
            f[i] = k * df;
        }
        return f;
    }

    /// <summary>
    /// A window of length <paramref name="n"/>, periodic unless <paramref name="symmetric"/>.
    /// <paramref name="beta"/> is required for <see cref="WindowType.Kaiser"/> and not allowed otherwise.
    /// </summary>
    public static double[] Window(WindowType type, int n, bool symmetric = false, double? beta = null)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);
        if (type == WindowType.Kaiser)
        {
            if (beta is not >= 0)
                throw new ArgumentException("kaiser needs beta >= 0", nameof(beta));
        }
        else if (!CosineSums.ContainsKey(type))
            throw new ArgumentException($"unknown window {type}", nameof(type));
        else if (beta is not null)
            throw new ArgumentException("beta applies to the kaiser window only", nameof(beta));
        if (n <= 1)
            return n == 0 ? [] : [1.0];

        var w = new double[n];
        double d = symmetric ? n - 1 : n;
        if (type == WindowType.Kaiser)
        {
            double b = beta!.Value, norm = BesselI0(b);
            for (int i = 0; i < n; i++)
            {
                double r = 2.0 * i / d - 1.0;
                w[i] = BesselI0(b * Math.Sqrt(Math.Max(1.0 - r * r, 0.0))) / norm;
            }
            return w;
        }
        double[] a = CosineSums[type];
        for (int k = 0; k < a.Length; k++)
        {
            double sign = k % 2 == 0 ? 1.0 : -1.0;
            for (int i = 0; i < n; i++)
                w[i] += sign * a[k] * Math.Cos(2.0 * Math.PI * k * i / d);
        }
        return w;
    }

    /// <summary>Coherent gain and ENBW (in bins) of a window. The window must not sum to zero.</summary>
    public static WindowStats WindowStats(ReadOnlySpan<double> window)
    {
        if (window.IsEmpty)
            throw new ArgumentException("window must not be empty", nameof(window));
        double s = 0, s2 = 0;
        foreach (double v in window)
        {
            s += v;
            s2 += v * v;
        }
        if (s == 0)
            throw new ArgumentException("window sums to zero", nameof(window));
        int n = window.Length;
        return new WindowStats(s / n, n * s2 / (s * s));
    }

    /// <summary>
    /// Welch PSD of complex samples: two-sided, in shifted (ascending) order. Segment length defaults
    /// to the whole input, overlap to half a segment.
    /// </summary>
    public static SpectralDensity WelchPsd(ReadOnlySpan<Complex> samples, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann) =>
        Welch(samples, sampleRate, nperseg, noverlap, window, oneSided: false);

    /// <summary>
    /// Welch PSD of real samples: one-sided (bins 0 … ⌊N/2⌋, all but DC and Nyquist doubled) unless
    /// <paramref name="oneSided"/> is false, which gives the two-sided shifted PSD.
    /// </summary>
    public static SpectralDensity WelchPsd(ReadOnlySpan<double> samples, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, bool oneSided = true) =>
        Welch(ToComplex(samples), sampleRate, nperseg, noverlap, window, oneSided);

    private static SpectralDensity Welch(ReadOnlySpan<Complex> x, double sampleRate, int? nperseg,
        int? noverlap, WindowType window, bool oneSided)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(sampleRate);
        int n = nperseg ?? x.Length;
        if (n < 1)
            throw new ArgumentException("nperseg must be at least 1", nameof(nperseg));
        if (x.Length < n)
            throw new ArgumentException("fewer samples than nperseg", nameof(nperseg));
        int overlap = noverlap ?? n / 2;
        if (overlap < 0 || overlap >= n)
            throw new ArgumentException("noverlap must satisfy 0 <= noverlap < nperseg", nameof(noverlap));
        int step = n - overlap;
        int segments = (x.Length - n) / step + 1;
        double[] w = Window(window, n);
        if (w.All(v => v == 0))
            throw new ArgumentException($"{window} window of length {n} is all zeros", nameof(window));

        double sumSq = w.Sum(v => v * v);
        var acc = new double[n];
        var buf = new Complex[n];
        for (int s = 0; s < segments; s++)
        {
            var seg = x.Slice(s * step, n);
            for (int i = 0; i < n; i++)
                buf[i] = seg[i] * w[i];
            Transform(buf);
            for (int i = 0; i < n; i++)
                acc[i] += buf[i].Real * buf[i].Real + buf[i].Imaginary * buf[i].Imaginary;
        }
        double scale = 1.0 / (sampleRate * sumSq) / segments;

        double[] psd, freqs;
        if (oneSided)
        {
            int m = n / 2 + 1;
            int last = n % 2 == 0 ? m - 1 : m;
            psd = new double[m];
            freqs = new double[m];
            for (int k = 0; k < m; k++)
            {
                psd[k] = acc[k] * scale * (k >= 1 && k < last ? 2.0 : 1.0);
                freqs[k] = k * (sampleRate / n);
            }
        }
        else
        {
            psd = new double[n];
            for (int i = 0; i < n; i++)
                psd[i] = acc[(i + (n + 1) / 2) % n] * scale; // fftshift: index i holds bin i − ⌊n/2⌋
            freqs = FftFrequencies(n, sampleRate, shifted: true);
        }
        var stats = WindowStats(w);
        return new SpectralDensity(freqs, psd, sampleRate, n, segments, oneSided, sampleRate / n,
            stats.EnbwBins * sampleRate / n);
    }

    /// <summary>
    /// Occupied bandwidth by the ITU-R SM.328 β/2 method: the band with (1 − fraction)/2 of the power
    /// left out on each side. Bins are rectangles of the bin spacing; edges interpolate within a bin.
    /// </summary>
    public static OccupiedBandwidth OccupiedBandwidth(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        double fraction = 0.99)
    {
        if (!(fraction > 0 && fraction <= 1))
            throw new ArgumentException("fraction must be in (0, 1]", nameof(fraction));
        double delta = CheckBins(frequencies, psd);
        int n = psd.Length;
        var cum = new double[n + 1]; // cum[k] = power before bin k
        for (int k = 0; k < n; k++)
            cum[k + 1] = cum[k] + psd[k] * delta;
        double total = cum[n];
        if (!(total > 0))
            throw new ArgumentException("total power must be positive", nameof(psd));
        double loTarget = (1 - fraction) / 2 * total, hiTarget = (1 + fraction) / 2 * total;

        int kLo = 0;
        while (!(cum[kLo + 1] > loTarget))
            kLo++;
        int kHi = n - 1;
        while (!(cum[kHi] < hiTarget))
            kHi--;
        double lower = frequencies[kLo] - delta / 2 + (loTarget - cum[kLo]) / (psd[kLo] * delta) * delta;
        double upper = frequencies[kHi] - delta / 2 + (hiTarget - cum[kHi]) / (psd[kHi] * delta) * delta;
        return new OccupiedBandwidth(upper - lower, lower, upper, total, fraction);
    }

    /// <summary>The PSD integrated over [low, high]; bins count by the part of their width inside.</summary>
    public static double ChannelPower(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double low, double high)
    {
        if (!(double.IsFinite(low) && double.IsFinite(high) && low < high))
            throw new ArgumentException("need finite low < high", nameof(low));
        double delta = CheckBins(frequencies, psd);
        double sum = 0;
        for (int k = 0; k < psd.Length; k++)
        {
            double left = frequencies[k] - delta / 2;
            double overlap = Math.Max(Math.Min(left + delta, high) - Math.Max(left, low), 0.0);
            sum += psd[k] * delta * overlap / delta;
        }
        return sum;
    }

    /// <summary>Validates a PSD's bins and returns the bin spacing.</summary>
    private static double CheckBins(ReadOnlySpan<double> f, ReadOnlySpan<double> psd)
    {
        if (f.Length != psd.Length)
            throw new ArgumentException("frequencies and psd must have the same length", nameof(psd));
        if (f.Length < 2)
            throw new ArgumentException("need at least two bins", nameof(f));
        foreach (double p in psd)
            if (!(double.IsFinite(p) && p >= 0))
                throw new ArgumentException("psd must be finite and non-negative", nameof(psd));
        double delta = (f[^1] - f[0]) / (f.Length - 1);
        bool even = delta > 0;
        for (int i = 1; even && i < f.Length; i++)
            even = Math.Abs(f[i] - f[i - 1] - delta) <= 1e-6 * delta;
        if (!even)
            throw new ArgumentException("frequencies must be ascending and evenly spaced", nameof(f));
        return delta;
    }

    private static Complex[] ToComplex(ReadOnlySpan<double> x)
    {
        var c = new Complex[x.Length];
        for (int i = 0; i < x.Length; i++)
            c[i] = new Complex(x[i], 0);
        return c;
    }

    /// <summary>In-place forward DFT of any length ≥ 1.</summary>
    private static void Transform(Complex[] x)
    {
        int n = x.Length;
        if (n == 1)
            return;
        if (BitOperations.IsPow2(n))
            Radix2(x);
        else
            Bluestein(x);
    }

    /// <summary>Iterative radix-2 decimation-in-time FFT; length must be a power of two.</summary>
    private static void Radix2(Complex[] x)
    {
        int n = x.Length;
        for (int i = 1, j = 0; i < n; i++)
        {
            int bit = n >> 1;
            for (; (j & bit) != 0; bit >>= 1)
                j ^= bit;
            j ^= bit;
            if (i < j)
                (x[i], x[j]) = (x[j], x[i]);
        }
        var tw = new Complex[n / 2]; // tw[k] = e^{−j2πk/n}, each computed directly for accuracy
        for (int k = 0; k < tw.Length; k++)
        {
            var (sin, cos) = Math.SinCos(-2.0 * Math.PI * k / n);
            tw[k] = new Complex(cos, sin);
        }
        for (int len = 2; len <= n; len <<= 1)
        {
            int half = len >> 1, stride = n / len;
            for (int start = 0; start < n; start += len)
            {
                for (int k = 0; k < half; k++)
                {
                    Complex t = tw[k * stride] * x[start + k + half];
                    Complex u = x[start + k];
                    x[start + k] = u + t;
                    x[start + k + half] = u - t;
                }
            }
        }
    }

    /// <summary>Bluestein's chirp-z FFT for any length, via a power-of-two circular convolution.</summary>
    private static void Bluestein(Complex[] x)
    {
        int n = x.Length;
        int m = (int)BitOperations.RoundUpToPowerOf2((uint)(2 * n - 1));
        var chirp = new Complex[n]; // e^{−jπk²/n}, with k² reduced mod 2n so the angle stays small
        long twoN = 2L * n;
        for (int k = 0; k < n; k++)
        {
            long k2 = (long)k * k % twoN;
            var (sin, cos) = Math.SinCos(-Math.PI * k2 / n);
            chirp[k] = new Complex(cos, sin);
        }
        var a = new Complex[m];
        var b = new Complex[m];
        for (int k = 0; k < n; k++)
            a[k] = x[k] * chirp[k];
        b[0] = Complex.Conjugate(chirp[0]);
        for (int k = 1; k < n; k++)
            b[k] = b[m - k] = Complex.Conjugate(chirp[k]);
        Radix2(a);
        Radix2(b);
        for (int i = 0; i < m; i++)
            a[i] = Complex.Conjugate(a[i] * b[i]);
        Radix2(a); // inverse via conjugation: conv = conj(FFT(conj(A·B))) / m
        for (int k = 0; k < n; k++)
            x[k] = Complex.Conjugate(a[k]) / m * chirp[k];
    }

    /// <summary>Modified Bessel function of the first kind, order 0, by its power series.</summary>
    internal static double BesselI0(double x)
    {
        double q = x * x / 4, term = 1, sum = 1;
        for (int k = 1; k < 500; k++)
        {
            term *= q / ((double)k * k);
            sum += term;
            if (term <= sum * 1e-17)
                break;
        }
        return sum;
    }
}
