namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Eberhardt's index of the <paramref name="pointDistances"/> (from random points
    /// to the nearest individual): n times the sum of squares over the square of the sum;
    /// about 4/pi at random, larger clumped (conventions: Eberhardt's index;
    /// ADR 0620).</summary>
    /// <param name="pointDistances">The distances from random points to the nearest
    /// individual, finite and at least 0, with a value above 0.</param>
    /// <returns>Eberhardt's index, in [1, n].</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double EberhardtIndex(ReadOnlySpan<double> pointDistances)
    {
        double top = 0;
        foreach (double v in pointDistances)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException("pointDistances must be finite and at least 0", nameof(pointDistances));
            top = Math.Max(top, v);
        }
        if (!(top > 0))
            throw new ArgumentException("pointDistances must have a value above 0", nameof(pointDistances));
        double s1 = 0;
        double s2 = 0;
        foreach (double v in pointDistances)
        {
            double u = v / top;
            s1 += u;
            s2 += u * u;
        }
        int n = pointDistances.Length;
        return Math.Clamp(n * s2 / (s1 * s1), 1.0, n);
    }
}
