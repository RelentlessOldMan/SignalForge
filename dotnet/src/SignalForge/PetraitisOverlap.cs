namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Petraitis' specific overlap of the record <paramref name="x"/> on the record
    /// <paramref name="y"/>, of values at least 0, each with a value above 0:
    /// exp(sum(p*(ln q - ln p))) over the kinds x uses, on their shares, from 0 to 1
    /// (conventions: Petraitis' specific overlap; ADR 0599).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Petraitis' specific overlap, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PetraitisOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double topX = PiankaTop(x, nameof(x));
        double topY = PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double sx = 0, sy = 0;
        for (int i = 0; i < x.Length; i++)
        {
            sx += x[i] / topX;
            sy += y[i] / topY;
        }
        double total = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (!(x[i] > 0))
                continue;
            double p = x[i] / topX / sx;
            double q = y[i] / topY / sy;
            if (!(q > 0))
                return 0.0;
            total += p * (Math.Log(q) - Math.Log(p));
        }
        return Math.Min(Math.Exp(total), 1.0);
    }
}
