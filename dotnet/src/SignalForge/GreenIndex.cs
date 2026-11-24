namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Green's index of dispersion of <paramref name="counts"/> of individuals in at
    /// least two sampling units, whole numbers at least 0 with a total above 1:
    /// (s^2/m - 1)/(sum(x) - 1), about 0 for counts at random and 1 for all in one unit
    /// (conventions: Green's index of dispersion; ADR 0611).</summary>
    /// <param name="counts">The counts, at least two, finite whole numbers at least 0, with a
    /// total above 1.</param>
    /// <returns>Green's index of dispersion, from -1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GreenIndex(ReadOnlySpan<double> counts)
    {
        if (counts.Length < 2)
            throw new ArgumentException("counts must have at least two units", nameof(counts));
        double top = 0;
        foreach (double v in counts)
        {
            if (!double.IsFinite(v) || v < 0 || v != Math.Floor(v))
                throw new ArgumentException("counts must be finite whole numbers at least 0", nameof(counts));
            top = Math.Max(top, v);
        }
        if (!(top > 0))
            throw new ArgumentException("counts must have a total above 0", nameof(counts));
        double s1 = 0, s2 = 0;
        foreach (double v in counts)
        {
            double u = v / top;
            s1 += u;
            s2 += u * u;
        }
        if (!(s1 * top > 1))
            throw new ArgumentException("counts must have a total above 1", nameof(counts));
        int n = counts.Length;
        double g = ((n * (s2 / s1) - s1) / (n - 1) - 1.0 / top) / (s1 - 1.0 / top);
        return Math.Min(Math.Max(g, -1.0), 1.0);
    }
}
