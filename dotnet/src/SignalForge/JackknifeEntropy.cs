namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The jackknife Shannon entropy of a record of whole numbers at least 0
    /// totalling more than 1, in nats: Zahl's jackknife over individuals of the plug-in
    /// entropy (conventions: the jackknife Shannon entropy; ADR 0558).</summary>
    /// <param name="samples">Whole numbers at least 0, totalling more than 1 and at most
    /// 10 000 000.</param>
    /// <returns>The jackknife Shannon entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double JackknifeEntropy(ReadOnlySpan<double> samples)
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
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        double sLog = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                sLog += v * Math.Log(v);
        }
        double rest = total - 1.0;
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double less = v - 1.0;
                double drop = sLog - (v * Math.Log(v));
                if (less > 0)
                    drop += less * Math.Log(less);
                acc += v * (Math.Log(rest) - (drop / rest));
            }
        }
        return (total * (Math.Log(total) - (sLog / total))) - (rest / total * acc);
    }
}
