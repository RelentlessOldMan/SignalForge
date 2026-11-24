namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Clark-Evans test statistic of the nearest-neighbour
    /// <paramref name="distances"/> of a pattern with <paramref name="density"/> individuals
    /// per unit area: (mean - 1/(2 sqrt(density)))/sigma, with sigma the standard error of the
    /// mean for individuals placed at random; about standard normal at random (conventions:
    /// the Clark-Evans test statistic; ADR 0617).</summary>
    /// <param name="distances">The distance from each individual to its nearest neighbour,
    /// finite and at least 0, not empty.</param>
    /// <param name="density">The individuals per unit area, finite and above 0.</param>
    /// <returns>The Clark-Evans test statistic.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the statistic
    /// overflows.</exception>
    public static double ClarkEvansZ(ReadOnlySpan<double> distances, double density)
    {
        double ratio = ClarkEvansRatio(distances, density);
        double z = (ratio - 1.0) * Math.Sqrt(distances.Length * Math.PI / (4.0 - Math.PI));
        if (!double.IsFinite(z))
            throw new ArgumentException("the statistic overflows", nameof(distances));
        return z;
    }
}
