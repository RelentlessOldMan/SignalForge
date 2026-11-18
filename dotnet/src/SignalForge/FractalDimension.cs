namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Katz's fractal dimension <c>log10 n / (log10 n + log10(d/L))</c> of the points
    /// <c>(i, x[i])</c> (conventions: Katz fractal dimension; ADR 0334).</summary>
    /// <param name="samples">Real samples, finite, at least 3.</param>
    /// <returns>The dimension.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or <c>n·d ≤ L</c>.</exception>
    public static double KatzDimension(ReadOnlySpan<double> samples)
    {
        CheckAtLeastThreeFinite(samples);
        int n = samples.Length - 1;
        double length = 0, extent = 0;
        for (int i = 0; i < n; i++)
        {
            double step = samples[i + 1] - samples[i];
            length += Math.Sqrt(1 + (step * step));
        }
        for (int i = 0; i <= n; i++)
        {
            double dy = samples[i] - samples[0];
            extent = Math.Max(extent, Math.Sqrt(((double)i * i) + (dy * dy)));
        }
        double denominator = Math.Log10(n) + Math.Log10(extent / length);
        if (!(denominator > 0))
            throw new ArgumentException("n·d must exceed L for the Katz dimension to be defined", nameof(samples));
        return Math.Log10(n) / denominator;
    }

    /// <summary>Petrosian's fractal dimension <c>log10 n / (log10 n + log10(n/(n + 0.4·N_Δ)))</c>
    /// with <c>N_Δ</c> the sign changes of the first difference (conventions: Petrosian fractal
    /// dimension; ADR 0335).</summary>
    /// <param name="samples">Real samples, finite, at least 3.</param>
    /// <returns>The dimension.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PetrosianDimension(ReadOnlySpan<double> samples)
    {
        CheckAtLeastThreeFinite(samples);
        int n = samples.Length;
        int changes = 0;
        for (int i = 0; i + 2 < n; i++)
        {
            if (Math.Sign(samples[i + 1] - samples[i]) * Math.Sign(samples[i + 2] - samples[i + 1]) < 0)
                changes++;
        }
        return Math.Log10(n) / (Math.Log10(n) + Math.Log10(n / (n + (0.4 * changes))));
    }

    private static void CheckAtLeastThreeFinite(ReadOnlySpan<double> samples)
    {
        if (samples.Length < 3)
            throw new ArgumentException("needs at least 3 samples", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
    }
}
