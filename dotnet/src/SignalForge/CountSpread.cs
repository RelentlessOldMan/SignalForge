namespace SignalForge;

public static partial class Measurements
{
    // The sum of the counts over top and the sum of the squared deviations from their mean
    // over top, each in record order: two passes, so a mean large next to the spread does
    // not cancel (conventions: Green's index).
    private static (double S1, double W) CountSpread(ReadOnlySpan<double> counts, double top)
    {
        double s1 = 0;
        foreach (double v in counts)
            s1 += v / top;
        double mean = top * (s1 / counts.Length);
        double w = 0;
        foreach (double v in counts)
        {
            double e = (v - mean) / top;
            w += e * e;
        }
        return (s1, w);
    }
}
