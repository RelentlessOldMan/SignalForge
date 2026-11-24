namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Clark-Evans aggregation index of the nearest-neighbour
    /// <paramref name="distances"/> of a pattern with <paramref name="density"/> individuals
    /// per unit area: the mean distance over 1/(2 sqrt(density)), its mean for individuals
    /// placed at random; 1 at random, below 1 clumped (conventions: the Clark-Evans
    /// aggregation index; ADR 0616).</summary>
    /// <param name="distances">The distance from each individual to its nearest neighbour,
    /// finite and at least 0, not empty.</param>
    /// <param name="density">The individuals per unit area, finite and above 0.</param>
    /// <returns>The Clark-Evans aggregation index, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the index
    /// overflows.</exception>
    public static double ClarkEvansRatio(ReadOnlySpan<double> distances, double density)
    {
        if (distances.IsEmpty)
            throw new ArgumentException("distances must not be empty", nameof(distances));
        double top = 0;
        foreach (double v in distances)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException("distances must be finite and at least 0", nameof(distances));
            top = Math.Max(top, v);
        }
        if (!double.IsFinite(density) || !(density > 0))
            throw new ArgumentException("density must be finite and above 0", nameof(density));
        if (top == 0)
            return 0.0;
        double s1 = 0;
        foreach (double v in distances)
            s1 += v / top;
        double r = (top * (s1 / distances.Length)) * (2.0 * Math.Sqrt(density));
        if (!double.IsFinite(r))
            throw new ArgumentException("the index overflows", nameof(distances));
        return r;
    }
}
