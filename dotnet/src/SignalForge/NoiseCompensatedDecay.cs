using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Schroeder decay with the mean power of the last <paramref name="tail"/> of
    /// the response subtracted before integrating, up to that noise window (conventions:
    /// Noise-compensated decay; ADR 0183).</summary>
    /// <param name="impulseResponse">Complex response, finite, not empty.</param>
    /// <param name="tail">The fraction of the response at its end that estimates the noise, in (0, 1).</param>
    /// <returns>The decay in dB for each sample before the noise window; <c>−∞</c> where the
    /// compensated energy is not positive.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] NoiseCompensatedDecay(ReadOnlySpan<Complex> impulseResponse, double tail = 0.1) =>
        CompensatedDecay(ResponsePowers(impulseResponse), tail);

    /// <summary>The Schroeder decay with the mean power of the last <paramref name="tail"/> of
    /// the response subtracted before integrating, up to that noise window (conventions:
    /// Noise-compensated decay; ADR 0183).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty.</param>
    /// <param name="tail">The fraction of the response at its end that estimates the noise, in (0, 1).</param>
    /// <returns>The decay in dB for each sample before the noise window; <c>−∞</c> where the
    /// compensated energy is not positive.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] NoiseCompensatedDecay(ReadOnlySpan<double> impulseResponse, double tail = 0.1) =>
        CompensatedDecay(ResponsePowers(impulseResponse), tail);

    private static double[] CompensatedDecay(double[] p, double tail)
    {
        if (!(double.IsFinite(tail) && tail > 0 && tail < 1))
            throw new ArgumentOutOfRangeException(nameof(tail), tail, "must be finite and in (0, 1)");
        int n = p.Length;
        double mm = Math.Floor(tail * n + 0.5);
        if (!(mm >= 1 && mm < n))
            throw new ArgumentOutOfRangeException(nameof(tail), tail, "tail * length must round to between 1 and length - 1 samples");
        int m = (int)mm;
        double noise = 0;
        for (int k = n - m; k < n; k++)
            noise += p[k];
        noise /= m;
        var energy = new double[n - m];
        double sum = 0;
        for (int k = n - m - 1; k >= 0; k--)
            energy[k] = sum += p[k] - noise;
        if (!(energy[0] > 0))
            throw new ArgumentException("impulseResponse must have energy above the noise", nameof(p));
        var d = new double[n - m];
        for (int k = 0; k < d.Length; k++)
            d[k] = energy[k] > 0 ? 10 * Math.Log10(energy[k] / energy[0]) : double.NegativeInfinity;
        return d;
    }
}
