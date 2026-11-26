namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Fisher's index of dispersion statistic of <paramref name="counts"/> of
    /// individuals in at least two sampling units, whole numbers at least 0 with a total above
    /// 0: sum((x - m)^2)/m, about chi-square with n - 1 degrees of freedom for counts at random
    /// (conventions: Fisher's index of dispersion statistic; ADR 0615).</summary>
    /// <param name="counts">The counts, at least two, finite whole numbers at least 0, with a
    /// total above 0.</param>
    /// <returns>Fisher's index of dispersion statistic, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the statistic
    /// overflows.</exception>
    public static double FisherDispersion(ReadOnlySpan<double> counts)
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
        (double s1, double w) = CountSpread(counts, top);
        int n = counts.Length;
        double d = top * (w * (n / s1));
        if (!double.IsFinite(d))
            throw new ArgumentException("the statistic overflows", nameof(counts));
        return d;
    }
}
