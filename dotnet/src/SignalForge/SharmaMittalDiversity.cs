namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Sharma-Mittal diversity of order <paramref name="order"/> and degree
    /// <paramref name="degree"/> of a record of values at least 0, not all 0: the Renyi
    /// diversity at degree 1, the Tsallis diversity at degree equal to order (conventions: the
    /// Sharma-Mittal diversity of counts; ADR 0570).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <param name="degree">The degree r, finite.</param>
    /// <returns>The Sharma-Mittal diversity.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SharmaMittalDiversity(ReadOnlySpan<double> samples, double order, double degree)
    {
        if (!double.IsFinite(degree))
            throw new ArgumentException("degree must be finite", nameof(degree));
        double h = RenyiDiversity(samples, order);
        if (degree == 1)
            return h;
        double x = (1.0 - degree) * h;
        double e = Math.Exp(x);
        double em1 = double.IsInfinity(e) ? e : Spectral.ExpM1(x);
        return em1 / (1.0 - degree);
    }
}
