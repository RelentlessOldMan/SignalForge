namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The energy-time curve <c>10·log10(|z|²/max|z|²)</c> with <c>z</c> the analytic
    /// signal (conventions: Energy-time curve; ADR 0186).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty, not all zero.</param>
    /// <returns>The curve in dB, one value per sample; the peak is 0 and zero is −∞.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] EnergyTimeCurve(ReadOnlySpan<double> impulseResponse)
    {
        var z = Spectral.AnalyticSignal(impulseResponse);
        var p = new double[z.Length];
        double peak = 0;
        for (int n = 0; n < z.Length; n++)
        {
            p[n] = z[n].Real * z[n].Real + z[n].Imaginary * z[n].Imaginary;
            peak = Math.Max(peak, p[n]);
        }
        if (!(peak > 0))
            throw new ArgumentException("impulse_response must not be all zero", nameof(impulseResponse));
        for (int n = 0; n < p.Length; n++)
            p[n] = 10 * Math.Log10(p[n] / peak);
        return p;
    }
}
