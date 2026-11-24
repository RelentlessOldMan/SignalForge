namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Savage's selection ratio of the record of use <paramref name="x"/> against the
    /// record of availability <paramref name="available"/>, of values at least 0, each with a
    /// value above 0 and <paramref name="available"/> above 0 everywhere: p/r on their shares
    /// for each kind, 1 for a kind used as it is available (conventions: Savage's selection
    /// ratio; ADR 0606).</summary>
    /// <param name="x">The record of use, finite, at least 0, with a value above 0.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <returns>Savage's selection ratio for each kind.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, an availability share
    /// underflows to 0, or a ratio overflows.</exception>
    public static double[] SavageSelectionRatio(ReadOnlySpan<double> x, ReadOnlySpan<double> available)
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
        double sx = 0, sa = 0;
        for (int i = 0; i < x.Length; i++)
        {
            sx += x[i] / topX;
            sa += available[i] / topA;
        }
        var ratios = new double[x.Length];
        for (int i = 0; i < x.Length; i++)
        {
            double share = available[i] / topA / sa;
            if (!(share > 0))
                throw new ArgumentException("available is too uneven: a share underflows to 0", nameof(available));
            ratios[i] = x[i] / topX / sx / share;
            if (!double.IsFinite(ratios[i]))
                throw new ArgumentException("a ratio overflows", nameof(available));
        }
        return ratios;
    }
}
