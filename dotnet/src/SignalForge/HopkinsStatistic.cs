namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hopkins' statistic: the sum of the squared <paramref name="pointDistances"/>
    /// over that sum plus the sum of the squared <paramref name="individualDistances"/>;
    /// about 1/2 at random, near 1 clumped (conventions: Hopkins' statistic;
    /// ADR 0618).</summary>
    /// <param name="pointDistances">The distances from random points to the nearest
    /// individual, finite and at least 0, not empty, with a value above 0.</param>
    /// <param name="individualDistances">The distances from individuals to their nearest
    /// neighbour, finite and at least 0, not empty, with a value above 0.</param>
    /// <returns>Hopkins' statistic, in [0, 1].</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HopkinsStatistic(ReadOnlySpan<double> pointDistances, ReadOnlySpan<double> individualDistances)
    {
        double top = Math.Max(
            HopkinsSampleTop(pointDistances, nameof(pointDistances)),
            HopkinsSampleTop(individualDistances, nameof(individualDistances)));
        double a = 0;
        foreach (double v in pointDistances)
        {
            double q = v / top;
            a += q * q;
        }
        double b = 0;
        foreach (double v in individualDistances)
        {
            double q = v / top;
            b += q * q;
        }
        return Math.Clamp(a / (a + b), 0.0, 1.0);
    }

    private static double HopkinsSampleTop(ReadOnlySpan<double> x, string name)
    {
        if (x.IsEmpty)
            throw new ArgumentException($"{name} must not be empty", name);
        double top = 0;
        foreach (double v in x)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException($"{name} must be finite and at least 0", name);
            top = Math.Max(top, v);
        }
        if (top == 0)
            throw new ArgumentException($"{name} must have a value above 0", name);
        return top;
    }
}
