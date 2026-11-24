namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hurlbert's niche breadth of the record of use <paramref name="x"/> against the
    /// record of availability <paramref name="available"/>, of values at least 0, each with a
    /// value above 0 and <paramref name="available"/> above 0 everywhere: 1/sum(p*p/r) on
    /// their shares, from the smallest share of availability to 1, or with
    /// <paramref name="standardized"/> from 0 to 1 (conventions: Hurlbert's niche breadth;
    /// ADR 0601).</summary>
    /// <param name="x">The record of use, finite, at least 0, with a value above 0.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <param name="standardized">Whether to give (B' - r_min)/(1 - r_min), which needs at
    /// least two kinds.</param>
    /// <returns>Hurlbert's niche breadth.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, an availability share
    /// underflows to 0, or the sum overflows.</exception>
    public static double HurlbertNicheBreadth(ReadOnlySpan<double> x, ReadOnlySpan<double> available, bool standardized = false)
    {
        double topX = PiankaTop(x, nameof(x));
        double topA = PiankaTop(available, nameof(available));
        foreach (double v in available)
        {
            if (!(v > 0))
                throw new ArgumentException("available must be above 0 everywhere", nameof(available));
        }
        if (x.Length != available.Length)
            throw new ArgumentException("x and available must have the same length", nameof(available));
        if (standardized && x.Length < 2)
            throw new ArgumentException("the standardized form needs at least two kinds", nameof(x));
        double sx = 0, sa = 0;
        for (int i = 0; i < x.Length; i++)
        {
            sx += x[i] / topX;
            sa += available[i] / topA;
        }
        double total = 0, least = 1.0;
        for (int i = 0; i < x.Length; i++)
        {
            double share = available[i] / topA / sa;
            if (!(share > 0))
                throw new ArgumentException("available is too uneven: a share underflows to 0", nameof(available));
            least = Math.Min(least, share);
            double p = x[i] / topX / sx;
            total += p * p / share;
        }
        if (!double.IsFinite(total))
            throw new ArgumentException("the sum overflows", nameof(available));
        double breadth = Math.Min(1.0 / total, 1.0);
        if (!standardized)
            return breadth;
        return Math.Min(Math.Max((breadth - least) / (1.0 - least), 0.0), 1.0);
    }
}
