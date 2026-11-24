namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Lloyd's mean crowding of <paramref name="counts"/> of individuals in sampling
    /// units, whole numbers at least 0 with a total above 0: sum(x (x - 1))/sum(x), the mean
    /// number of others in an individual's unit (conventions: Lloyd's mean crowding;
    /// ADR 0609).</summary>
    /// <param name="counts">The counts, finite whole numbers at least 0, with a total above
    /// 0.</param>
    /// <returns>Lloyd's mean crowding, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LloydMeanCrowding(ReadOnlySpan<double> counts)
    {
        if (counts.IsEmpty)
            throw new ArgumentException("counts must not be empty", nameof(counts));
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
        return Math.Max(top * (s2 / s1) - 1.0, 0.0);
    }
}
