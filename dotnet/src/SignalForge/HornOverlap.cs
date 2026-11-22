namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Horn's information overlap of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0: the information
    /// shared by the two records over its largest value for their totals, from 0 to 1
    /// (conventions: Horn's information overlap; ADR 0574).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The overlap, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HornOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double m = Math.Max(PiankaTop(x, nameof(x)), PiankaTop(y, nameof(y)));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double num = 0, tx = 0, ty = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double a = x[i] / m;
            double b = y[i] / m;
            num += HornTerm(a, b);
            tx += a;
            ty += b;
        }
        return Math.Min(num / HornTerm(tx, ty), 1.0);
    }

    // (a + b) ln(a + b) - a ln a - b ln b without cancellation; 0 when a or b is 0.
    static double HornTerm(double a, double b)
    {
        if (a == 0 || b == 0)
            return 0;
        return a * Spectral.LogP1(b / a) + b * Spectral.LogP1(a / b);
    }
}
