using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Schroeder's modulation transfer <c>|Σ |h[n]|²·e^{−j2πF n/fs}| / Σ |h[n]|²</c> for each
    /// frequency (conventions: Modulation transfer function; ADR 0176).</summary>
    /// <param name="impulseResponse">Complex response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="frequencies">Modulation frequencies in Hz, finite and non-negative, not empty.</param>
    /// <returns>One modulation factor per frequency, in order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ModulationTransfer(ReadOnlySpan<Complex> impulseResponse, double sampleRate, ReadOnlySpan<double> frequencies) =>
        Modulation(ResponsePowers(impulseResponse), sampleRate, frequencies);

    /// <summary>Schroeder's modulation transfer <c>|Σ h[n]²·e^{−j2πF n/fs}| / Σ h[n]²</c> for each
    /// frequency (conventions: Modulation transfer function; ADR 0176).</summary>
    /// <param name="impulseResponse">Real response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="frequencies">Modulation frequencies in Hz, finite and non-negative, not empty.</param>
    /// <returns>One modulation factor per frequency, in order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ModulationTransfer(ReadOnlySpan<double> impulseResponse, double sampleRate, ReadOnlySpan<double> frequencies) =>
        Modulation(ResponsePowers(impulseResponse), sampleRate, frequencies);

    private static double[] Modulation(double[] p, double sampleRate, ReadOnlySpan<double> frequencies)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (frequencies.IsEmpty)
            throw new ArgumentException("frequencies must not be empty", nameof(frequencies));
        foreach (double f in frequencies)
        {
            if (!(double.IsFinite(f) && f >= 0))
                throw new ArgumentException("frequencies must be finite and non-negative", nameof(frequencies));
        }
        double total = 0;
        foreach (double v in p)
            total += v;
        if (!(total > 0))
            throw new ArgumentException("impulseResponse must not be all zero", nameof(p));
        var m = new double[frequencies.Length];
        for (int k = 0; k < m.Length; k++)
        {
            double re = 0, im = 0;
            for (int n = 0; n < p.Length; n++)
            {
                double phase = 2 * Math.PI * frequencies[k] * n / sampleRate;
                re += p[n] * Math.Cos(phase);
                im += p[n] * Math.Sin(phase);
            }
            m[k] = double.Hypot(re, im) / total;
        }
        return m;
    }
}
