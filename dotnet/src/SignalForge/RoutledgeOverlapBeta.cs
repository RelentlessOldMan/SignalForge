namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Routledge's overlap beta of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0:
    /// 2bc/((a + b + c)^2 - 2bc) on the kinds above 0, from 0 to 1 (conventions: Routledge's
    /// overlap beta; ADR 0597).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Routledge's overlap beta, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RoutledgeOverlapBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int both = 0, onlyX = 0, onlyY = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] > 0 && y[i] > 0)
                both++;
            else if (x[i] > 0)
                onlyX++;
            else if (y[i] > 0)
                onlyY++;
        }
        long pooled = (long)both + onlyX + onlyY;
        long apart = 2L * onlyX * onlyY;
        return (double)apart / (pooled * pooled - apart);
    }
}
