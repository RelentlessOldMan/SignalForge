namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Divides each value by the largest one, when that is positive and finite, so no
    /// sum of the shares can overflow; otherwise returns the values unchanged for the caller's
    /// own checks to refuse (ADR 0625).</summary>
    private static ReadOnlySpan<double> ScaledToLargest(ReadOnlySpan<double> samples)
    {
        double top = 0;
        foreach (double v in samples)
        {
            if (v > top)
                top = v;
        }
        if (!(top > 0) || double.IsInfinity(top))
            return samples;
        double[] scaled = new double[samples.Length];
        for (int i = 0; i < samples.Length; i++)
            scaled[i] = samples[i] / top;
        return scaled;
    }
}
