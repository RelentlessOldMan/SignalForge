namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Gleason's index of a record of values at least 0 totalling more than 1: the
    /// count of values above 0 over the logarithm of the total (conventions: Gleason's
    /// index; ADR 0543).</summary>
    /// <param name="samples">Real values, finite, at least 0, totalling more than 1.</param>
    /// <returns>Gleason's index, above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GleasonIndex(ReadOnlySpan<double> samples)
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
            total += v;
        }
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        return k / Math.Log(total);
    }
}
