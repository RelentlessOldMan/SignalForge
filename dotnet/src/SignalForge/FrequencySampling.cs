using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Symmetric or antisymmetric FIR taps from a piecewise-linear gain sampled from 0 to
    /// sampleRate/2, inverse DFT with linear phase, then the symmetric window; no rescaling
    /// (conventions: FIR filters, Frequency-sampling design; ADR 0084, ADR 0085).</summary>
    /// <param name="numTaps">Number of taps: at least 1 for a filter, whose even lengths need zero gain at
    /// sampleRate/2; at least 2 for the antisymmetric kinds, whose odd lengths need zero gain at sampleRate/2.</param>
    /// <param name="frequencies">Breakpoints in Hz, strictly increasing from exactly 0 to exactly sampleRate/2.</param>
    /// <param name="gains">The gain at each breakpoint; linear between them.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="window">Window, in its symmetric form.</param>
    /// <param name="beta">Kaiser β; only with <see cref="WindowType.Kaiser"/>.</param>
    /// <param name="numPoints">Grid points K from 0 to sampleRate/2, in [2, 2²⁰ + 1] with 2(K − 1) ≥ numTaps;
    /// null for K − 1 the smallest power of two at least max(numTaps, 512).</param>
    /// <param name="kind">Symmetric filter, or antisymmetric Hilbert (zero gain at 0 required) or
    /// differentiator (amplitude −2πν·gain), as for <see cref="FirEquiripple"/>.</param>
    public static double[] FirFrequencySampling(int numTaps, IReadOnlyList<double> frequencies, IReadOnlyList<double> gains,
        double sampleRate, WindowType window = WindowType.Hamming, double? beta = null, int? numPoints = null,
        FirKind kind = FirKind.Filter)
    {
        ArgumentNullException.ThrowIfNull(frequencies);
        ArgumentNullException.ThrowIfNull(gains);
        int n = numTaps;
        if (n < 1)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "must be at least 1");
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (frequencies.Count < 2 || frequencies.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("frequencies must be at least two finite values", nameof(frequencies));
        if (frequencies[0] != 0 || frequencies[^1] != fs / 2
            || Enumerable.Range(1, frequencies.Count - 1).Any(i => frequencies[i] <= frequencies[i - 1]))
            throw new ArgumentException("frequencies must increase strictly from 0 to sampleRate/2", nameof(frequencies));
        if (gains.Count != frequencies.Count || gains.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("gains must have one finite value per frequency", nameof(gains));
        if (!Enum.IsDefined(kind))
            throw new ArgumentOutOfRangeException(nameof(kind), kind, "unknown kind");
        bool anti = kind != FirKind.Filter;
        if (anti && n < 2)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "an antisymmetric kind needs at least 2");
        if (!anti && n % 2 == 0 && gains[^1] != 0)
            throw new ArgumentException("an even numTaps needs zero gain at sampleRate/2", nameof(gains));
        if (anti && n % 2 == 1 && gains[^1] != 0)
            throw new ArgumentException("an odd antisymmetric design needs zero gain at sampleRate/2", nameof(gains));
        if (kind == FirKind.Hilbert && gains[0] != 0)
            throw new ArgumentException("a Hilbert design needs zero gain at 0", nameof(gains));
        int k;
        if (numPoints is int given)
        {
            if (given < 2 || given > (1 << 20) + 1)
                throw new ArgumentOutOfRangeException(nameof(numPoints), given, "must be in [2, 2^20 + 1]");
            k = given;
        }
        else
        {
            if (n > 1 << 30)
                throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "too many taps for the default grid");
            k = 1;
            while (k < Math.Max(n, 512))
                k <<= 1;
            k += 1;
        }
        long l = 2L * (k - 1);
        if (l < n)
            throw new ArgumentException("2*(numPoints - 1) must be at least numTaps", nameof(numPoints));
        double[] w = Spectral.Window(window, n, symmetric: true, beta);

        var spectrum = new Complex[l];
        int seg = 0;
        for (int j = 0; j < k; j++)
        {
            double nu = j / (double)l;
            while (seg < frequencies.Count - 2 && frequencies[seg + 1] / fs < nu)
                seg++;
            double lo = frequencies[seg] / fs, hi = frequencies[seg + 1] / fs;
            double g = gains[seg] + ((gains[seg + 1] - gains[seg]) * (nu - lo) / (hi - lo));
            if (kind == FirKind.Differentiator)
                g = -2 * Math.PI * nu * g;
            Complex v = g * Complex.FromPolarCoordinates(1, -Math.PI * j * (n - 1) / l);
            if (anti)
                v *= -Complex.ImaginaryOne;
            spectrum[j] = v;
            if (j > 0 && j < k - 1)
                spectrum[l - j] = Complex.Conjugate(v);
        }
        spectrum[0] = spectrum[0].Real; // the Hermitian extension's real DC and Nyquist bins
        spectrum[k - 1] = spectrum[k - 1].Real;
        Complex[] x = Spectral.Ifft(spectrum);
        var d = new double[n];
        for (int i = 0; i < n; i++)
            d[i] = x[i].Real * w[i];
        var h = new double[n];
        for (int i = 0; i < n; i++)
            h[i] = anti ? (d[i] - d[n - 1 - i]) / 2 : (d[i] + d[n - 1 - i]) / 2;
        return h;
    }
}
