namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The interaural cross-correlation <c>max |Σ l[n]·r[n+τ]| / √(E_l·E_r)</c> over
    /// integer lags <c>|τ| ≤ ⌊maxLag·fs + 1/2⌋</c> (conventions: Interaural cross-correlation;
    /// ADR 0174).</summary>
    /// <param name="left">The left response, finite, not all zero.</param>
    /// <param name="right">The right response, the same length, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="maxLag">The largest lag in seconds, finite and non-negative.</param>
    /// <returns>The IACC, in [0, 1].</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Iacc(ReadOnlySpan<double> left, ReadOnlySpan<double> right, double sampleRate, double maxLag = 0.001)
    {
        if (left.IsEmpty || left.Length != right.Length)
            throw new ArgumentException("left and right must be non-empty and of equal length", nameof(right));
        double el = 0, er = 0;
        for (int n = 0; n < left.Length; n++)
        {
            if (!(double.IsFinite(left[n]) && double.IsFinite(right[n])))
                throw new ArgumentException("left and right must be finite", nameof(left));
            el += left[n] * left[n];
            er += right[n] * right[n];
        }
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (!(double.IsFinite(maxLag) && maxLag >= 0))
            throw new ArgumentOutOfRangeException(nameof(maxLag), maxLag, "must be finite and non-negative");
        if (!(el > 0 && er > 0))
            throw new ArgumentException("left and right must not be all zero", nameof(left));
        int length = left.Length;
        double size = Math.Floor(maxLag * sampleRate + 0.5);
        int reach = size >= length - 1 ? length - 1 : (int)size;
        double best = 0;
        for (int t = -reach; t <= reach; t++)
        {
            double r = 0;
            for (int n = Math.Max(0, -t); n < Math.Min(length, length - t); n++)
                r += left[n] * right[n + t];
            best = Math.Max(best, Math.Abs(r));
        }
        return best / Math.Sqrt(el * er);
    }
}
