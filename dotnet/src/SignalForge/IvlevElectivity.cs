namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Ivlev's electivity of the record of use <paramref name="x"/> against the
    /// record of availability <paramref name="available"/>, of values at least 0, each with a
    /// value above 0 and <paramref name="available"/> above 0 everywhere: (p - r)/(p + r) on
    /// their shares for each kind, from -1 to 1 (conventions: Ivlev's electivity;
    /// ADR 0603).</summary>
    /// <param name="x">The record of use, finite, at least 0, with a value above 0.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <returns>Ivlev's electivity for each kind.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or an availability
    /// share underflows to 0.</exception>
    public static double[] IvlevElectivity(ReadOnlySpan<double> x, ReadOnlySpan<double> available)
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
        var result = new double[x.Length];
        for (int i = 0; i < x.Length; i++)
        {
            double share = available[i] / topA / sa;
            if (!(share > 0))
                throw new ArgumentException("available is too uneven: a share underflows to 0", nameof(available));
            double p = x[i] / topX / sx;
            result[i] = Math.Min(Math.Max((p - share) / (p + share), -1.0), 1.0);
        }
        return result;
    }
}
