namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Morisita's overlap of the count records <paramref name="x"/> and
    /// <paramref name="y"/>, whole numbers at least 0, each totalling from 2 to 10 000 000:
    /// 2 sum(x y)/((l_x + l_y) X Y) with the unbiased Simpson concentrations l, at least 0
    /// (conventions: Morisita's overlap of two count records; ADR 0581).</summary>
    /// <param name="x">The first record of counts, totalling from 2 to 10 000 000.</param>
    /// <param name="y">The second record of counts, totalling from 2 to 10 000 000, the same
    /// length as x.</param>
    /// <returns>The overlap, at least 0; near 1 for records of the same shares.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MorisitaOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double bigX = MorisitaTotal(x, nameof(x));
        double bigY = MorisitaTotal(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double cross = 0, sx = 0, sy = 0;
        for (int i = 0; i < x.Length; i++)
        {
            cross += x[i] * y[i];
            sx += x[i] * (x[i] - 1.0);
            sy += y[i] * (y[i] - 1.0);
        }
        double den = sx * (bigY * (bigY - 1.0)) + sy * (bigX * (bigX - 1.0));
        if (!(den > 0))
            throw new ArgumentException("x or y must hold a count above 1", nameof(y));
        return 2.0 * cross * (bigX - 1.0) * (bigY - 1.0) / den;
    }

    static double MorisitaTotal(ReadOnlySpan<double> values, string name)
    {
        if (values.Length < 1)
            throw new ArgumentException($"{name} must not be empty", name);
        double total = 0;
        foreach (double v in values)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException($"{name} must be finite and at least 0", name);
            if (v != Math.Floor(v))
                throw new ArgumentException($"{name} must be whole numbers", name);
            total += v;
        }
        if (total < 2)
            throw new ArgumentException($"{name} must total at least 2", name);
        if (total > 10_000_000)
            throw new ArgumentException($"{name} must total at most 10 000 000", name);
        return total;
    }
}
