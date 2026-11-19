namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Vargha–Delaney A: the probability that a value of <paramref name="x"/>
    /// exceeds a value of <paramref name="y"/>, ties counting half, over every pair
    /// (conventions: Vargha–Delaney A; ADR 0401).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The probability, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double VarghaDelaneyA(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var ys = y.ToArray();
        Array.Sort(ys);
        long wins = 0, ties = 0;
        foreach (double v in x)
        {
            int left = CliffBound(ys, v, false);
            wins += left;
            ties += CliffBound(ys, v, true) - left;
        }
        return (double)(2 * wins + ties) / (2L * x.Length * y.Length);
    }
}
