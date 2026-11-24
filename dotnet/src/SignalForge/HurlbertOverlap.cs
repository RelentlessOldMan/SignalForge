namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hurlbert's niche overlap of the records of use <paramref name="x"/> and
    /// <paramref name="y"/> against the record of availability <paramref name="available"/>,
    /// of values at least 0, each with a value above 0 and <paramref name="available"/> above
    /// 0 everywhere: sum(p*q/r) on their shares, 1 when both use the kinds as they are
    /// available (conventions: Hurlbert's niche overlap; ADR 0600).</summary>
    /// <param name="x">The first record of use, finite, at least 0, with a value above
    /// 0.</param>
    /// <param name="y">The second record of use, finite, at least 0, with a value above 0, the
    /// same length as x.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <returns>Hurlbert's niche overlap, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, an availability share
    /// underflows to 0, or the sum overflows.</exception>
    public static double HurlbertOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y, ReadOnlySpan<double> available)
    {
        double topX = PiankaTop(x, nameof(x));
        double topY = PiankaTop(y, nameof(y));
        double topA = PiankaTop(available, nameof(available));
        foreach (double v in available)
        {
            if (!(v > 0))
                throw new ArgumentException("available must be above 0 everywhere", nameof(available));
        }
        if (x.Length != y.Length || x.Length != available.Length)
            throw new ArgumentException("x, y and available must have the same length", nameof(available));
        double sx = 0, sy = 0, sa = 0;
        for (int i = 0; i < x.Length; i++)
        {
            sx += x[i] / topX;
            sy += y[i] / topY;
            sa += available[i] / topA;
        }
        double total = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double share = available[i] / topA / sa;
            if (!(share > 0))
                throw new ArgumentException("available is too uneven: a share underflows to 0", nameof(available));
            total += x[i] / topX / sx * (y[i] / topY / sy) / share;
        }
        if (!double.IsFinite(total))
            throw new ArgumentException("the overlap overflows", nameof(available));
        return total;
    }
}
