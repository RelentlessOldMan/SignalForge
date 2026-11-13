namespace SignalForge;

/// <summary>Errors over a compared span.</summary>
/// <param name="Errors">Number of positions that differ.</param>
/// <param name="Compared">Number of positions compared.</param>
/// <param name="Rate">Errors / Compared; NaN when nothing was compared.</param>
public sealed record ErrorCount(int Errors, int Compared, double Rate);

/// <summary>Error-rate metrics.</summary>
public static class Metrics
{
    /// <summary>Count differing bits between two equal-length bit sequences.</summary>
    public static ErrorCount BitErrors(ReadOnlySpan<byte> reference, ReadOnlySpan<byte> received)
    {
        if (reference.Length != received.Length)
            throw new ArgumentException(
                $"length mismatch: {reference.Length} reference vs {received.Length} received", nameof(received));
        int errors = 0;
        for (int i = 0; i < reference.Length; i++)
            if (reference[i] != received[i])
                errors++;
        int n = reference.Length;
        return new ErrorCount(errors, n, n > 0 ? (double)errors / n : double.NaN);
    }
}
