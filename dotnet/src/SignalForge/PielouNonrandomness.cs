namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Pielou's index of non-randomness of the <paramref name="pointDistances"/>
    /// (from random points to the nearest individual) of a pattern with
    /// <paramref name="density"/> individuals per unit area: pi density times the mean squared
    /// distance; 1 at random, above 1 clumped (conventions: Pielou's index of non-randomness;
    /// ADR 0619).</summary>
    /// <param name="pointDistances">The distances from random points to the nearest
    /// individual, finite and at least 0, not empty.</param>
    /// <param name="density">The individuals per unit area, finite and above 0.</param>
    /// <returns>Pielou's index of non-randomness, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the index
    /// overflows.</exception>
    public static double PielouNonrandomness(ReadOnlySpan<double> pointDistances, double density)
    {
        if (pointDistances.IsEmpty)
            throw new ArgumentException("pointDistances must not be empty", nameof(pointDistances));
        double top = 0;
        foreach (double v in pointDistances)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException("pointDistances must be finite and at least 0", nameof(pointDistances));
            top = Math.Max(top, v);
        }
        if (!double.IsFinite(density) || !(density > 0))
            throw new ArgumentException("density must be finite and above 0", nameof(density));
        if (top == 0)
            return 0.0;
        double s2 = 0;
        foreach (double v in pointDistances)
        {
            double u = v / top;
            s2 += u * u;
        }
        double p = (top * Math.Sqrt(s2 / pointDistances.Length)) * (Math.Sqrt(Math.PI) * Math.Sqrt(density));
        double r = p * p;
        if (!double.IsFinite(r))
            throw new ArgumentException("the index overflows", nameof(pointDistances));
        return r;
    }
}
