namespace SignalForge;

public static partial class Measurements
{
    // The sum of the counts over top and the sum of x (x - 1) over top squared, each in record
    // order: x - 1 is formed before scaling, so the many counts of 1 that make the index small
    // add exact zeros (conventions: Lloyd's mean crowding).
    private static (double S1, double C) CountPairs(ReadOnlySpan<double> counts, double top)
    {
        double s1 = 0, c = 0;
        foreach (double x in counts)
        {
            s1 += x / top;
            c += (x / top) * ((x - 1.0) / top);
        }
        return (s1, c);
    }
}
