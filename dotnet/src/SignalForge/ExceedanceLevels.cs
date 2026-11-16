namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The level exceeded <c>N</c> % of the time for each <c>N</c> in
    /// <paramref name="percents"/>: the <c>1 − N/100</c> quantile of <paramref name="powers"/> by
    /// linear interpolation (conventions: Exceedance levels; ADR 0169).</summary>
    /// <param name="powers">Powers, finite and non-negative, not empty.</param>
    /// <param name="percents">Percentages in [0, 100]; may be empty.</param>
    /// <returns>One power per percentage, in order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ExceedanceLevels(ReadOnlySpan<double> powers, ReadOnlySpan<double> percents)
    {
        if (powers.IsEmpty)
            throw new ArgumentException("powers must not be empty", nameof(powers));
        foreach (double v in powers)
            if (!(double.IsFinite(v) && v >= 0))
                throw new ArgumentException("powers must be finite and non-negative", nameof(powers));
        foreach (double v in percents)
            if (!(double.IsFinite(v) && v >= 0 && v <= 100))
                throw new ArgumentException("percents must be finite and in [0, 100]", nameof(percents));
        double[] s = powers.ToArray();
        Array.Sort(s);
        var output = new double[percents.Length];
        for (int i = 0; i < percents.Length; i++)
        {
            double h = (s.Length - 1) * (1 - percents[i] / 100);
            int k = Math.Min((int)Math.Floor(h), s.Length - 1);
            output[i] = k == s.Length - 1 ? s[k] : s[k] + (h - k) * (s[k + 1] - s[k]);
        }
        return output;
    }
}
