namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Bonachela entropy of a record of whole numbers at least 0, not all 0, in
    /// nats: the balanced small-sample estimate of Bonachela, Hinrichsen and Munoz
    /// (conventions: the Bonachela entropy; ADR 0560).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000.</param>
    /// <returns>The Bonachela entropy in nats, above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BonachelaEntropy(ReadOnlySpan<double> samples)
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
        HashSet<int> need = new();
        foreach (double v in samples)
        {
            if (v > 0)
                need.Add((int)v + 1);
        }
        Dictionary<int, double> marks = new();
        double harm = 0;
        int top = (int)total + 2;
        for (int j = 1; j <= top; j++)
        {
            harm += 1.0 / j;
            if (need.Contains(j))
                marks[j] = harm;
        }
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                acc += (v + 1.0) * (harm - marks[(int)v + 1]);
        }
        return acc / (total + 2.0);
    }
}
