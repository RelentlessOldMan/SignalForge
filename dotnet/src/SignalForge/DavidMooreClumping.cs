namespace SignalForge;

public static partial class Measurements
{
    /// <summary>David and Moore's index of clumping of <paramref name="counts"/> of
    /// individuals in at least two sampling units, whole numbers at least 0 with a total above
    /// 0: s^2/m - 1, about 0 for counts at random (conventions: David and Moore's index of
    /// clumping; ADR 0613).</summary>
    /// <param name="counts">The counts, at least two, finite whole numbers at least 0, with a
    /// total above 0.</param>
    /// <returns>David and Moore's index of clumping, at least -1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DavidMooreClumping(ReadOnlySpan<double> counts)
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
        int n = counts.Length;
        return Math.Max(top * ((n * (s2 / s1) - s1) / (n - 1)) - 1.0, -1.0);
    }
}
