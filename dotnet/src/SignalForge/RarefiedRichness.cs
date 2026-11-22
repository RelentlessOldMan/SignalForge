namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The rarefied richness of a record of whole numbers at least 0: the expected
    /// count of kinds among <paramref name="size"/> individuals drawn from them without
    /// replacement (conventions: the rarefied richness; ADR 0552).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000.</param>
    /// <param name="size">The number of individuals drawn, from 1 to the total.</param>
    /// <returns>The rarefied richness, from 1 to the count of values above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RarefiedRichness(ReadOnlySpan<double> samples, int size)
    {
        if (size < 1)
            throw new ArgumentException("size must be at least 1", nameof(size));
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
        if (size > total)
            throw new ArgumentException("size must be at most the total", nameof(size));
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double miss = 1.0;
                for (int j = 0; j < (int)v; j++)
                {
                    miss *= (total - size - j) / (total - j);
                    if (miss == 0)
                        break;
                }
                acc += 1.0 - miss;
            }
        }
        return acc;
    }
}
