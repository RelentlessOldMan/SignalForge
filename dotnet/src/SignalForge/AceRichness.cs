namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The ACE richness of a record of whole numbers at least 0: Chao and Lee's
    /// abundance-based coverage estimator, kinds with counts 1 to 10 as the rare group
    /// (conventions: the ACE richness; ADR 0551).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000; the values from 1 to 10, if any, not all 1.</param>
    /// <returns>The ACE richness, at least the count of values above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double AceRichness(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            if (v != Math.Floor(v))
                throw new ArgumentException("samples must be whole numbers", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        if (total > 10_000_000)
            throw new ArgumentException("samples must total at most 10 000 000", nameof(samples));
        int sAbund = 0;
        int sRare = 0;
        int ones = 0;
        double nRare = 0;
        double pairs = 0;
        foreach (double v in samples)
        {
            if (v > 10)
            {
                sAbund++;
            }
            else if (v > 0)
            {
                sRare++;
                nRare += v;
                pairs += v * (v - 1.0);
                if (v == 1)
                    ones++;
            }
        }
        if (sRare == 0)
            return sAbund;
        if (ones == sRare)
            throw new ArgumentException("samples must have a rare value above 1", nameof(samples));
        double cover = 1.0 - (ones / nRare);
        double gamma = Math.Max((sRare / cover * pairs / (nRare * (nRare - 1.0))) - 1.0, 0.0);
        return sAbund + (sRare / cover) + (ones / cover * gamma);
    }
}
