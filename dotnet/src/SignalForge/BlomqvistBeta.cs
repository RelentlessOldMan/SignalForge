namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Blomqvist's beta, the medial correlation: the share of samples on the same
    /// side of both medians less the share on opposite sides, samples on a median dropped
    /// (conventions: Blomqvist's beta; ADR 0375).</summary>
    /// <param name="x">Real samples, finite.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <returns>Beta, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or every sample lies
    /// on a median.</exception>
    public static double BlomqvistBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n == 0)
            throw new ArgumentException("x and y must not be empty", nameof(x));
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        double mx = SortedMedian(x.ToArray()), my = SortedMedian(y.ToArray());
        int agree = 0, disagree = 0;
        for (int i = 0; i < n; i++)
        {
            int p = Math.Sign(x[i] - mx) * Math.Sign(y[i] - my);
            if (p > 0)
                agree++;
            else if (p < 0)
                disagree++;
        }
        if (agree + disagree == 0)
            throw new ArgumentException("every sample lies on a median", nameof(x));
        return (double)(agree - disagree) / (agree + disagree);
    }
}
