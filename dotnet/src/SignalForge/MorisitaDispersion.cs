namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Morisita's index of dispersion of <paramref name="counts"/> of individuals in
    /// n sampling units, at least two, whole numbers at least 0 with a total above 1:
    /// n sum(x (x - 1))/(sum(x) (sum(x) - 1)), about 1 for counts at random and n for all in
    /// one unit (conventions: Morisita's index of dispersion; ADR 0612).</summary>
    /// <param name="counts">The counts, at least two, finite whole numbers at least 0, with a
    /// total above 1.</param>
    /// <returns>Morisita's index of dispersion, from 0 to n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MorisitaDispersion(ReadOnlySpan<double> counts)
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
        double d = n * (s2 - s1 / top) / (s1 * (s1 - 1.0 / top));
        return Math.Min(Math.Max(d, 0.0), n);
    }
}
