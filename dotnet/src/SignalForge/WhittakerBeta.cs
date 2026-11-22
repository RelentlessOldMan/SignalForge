namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Whittaker's beta diversity of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0:
    /// 2 S_union/(S_x + S_y) - 1 on the kinds above 0, from 0 to 1 (conventions: Whittaker's
    /// beta of two records; ADR 0575).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The beta diversity, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double WhittakerBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int both = 0, one = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] > 0 && y[i] > 0)
                both++;
            else if (x[i] > 0 || y[i] > 0)
                one++;
        }
        return (double)one / (2.0 * both + one);
    }
}
