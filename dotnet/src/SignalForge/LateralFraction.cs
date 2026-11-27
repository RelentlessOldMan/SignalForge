namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The lateral energy fraction <c>Σ_{N_a ≤ n &lt; N_b} h_8² / Σ_{n &lt; N_b} h_o²</c>,
    /// with <c>N = ⌊t·fs + 1/2⌋</c> (conventions: Lateral energy fraction; ADR 0175).</summary>
    /// <param name="omni">The omnidirectional response from index 0, finite.</param>
    /// <param name="figureEight">The figure-of-eight response, the same length, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="start">The start of the lateral window in seconds, finite, <c>≥ 0</c>.</param>
    /// <param name="stop">The end of both windows in seconds, finite, above <paramref name="start"/>.</param>
    /// <returns>The lateral fraction, not clamped (it can exceed 1).</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LateralFraction(
        ReadOnlySpan<double> omni, ReadOnlySpan<double> figureEight, double sampleRate, double start = 0.005, double stop = 0.08)
    {
        if (omni.IsEmpty || omni.Length != figureEight.Length)
            throw new ArgumentException("omni and figureEight must be non-empty and of equal length", nameof(figureEight));
        for (int n = 0; n < omni.Length; n++)
        {
            if (!(double.IsFinite(omni[n]) && double.IsFinite(figureEight[n])))
                throw new ArgumentException("omni and figureEight must be finite", nameof(omni));
        }
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (!(double.IsFinite(start) && start >= 0))
            throw new ArgumentOutOfRangeException(nameof(start), start, "must be finite and non-negative");
        if (!(double.IsFinite(stop) && stop > start))
            throw new ArgumentOutOfRangeException(nameof(stop), stop, "must be finite and above start");
        double sa = Math.Floor(start * sampleRate + 0.5);
        double sb = Math.Floor(stop * sampleRate + 0.5);
        if (sb < 1)
            throw new ArgumentOutOfRangeException(nameof(stop), stop, "stop * sampleRate must round to at least 1 sample");
        int na = sa >= omni.Length ? omni.Length : (int)sa;
        int nb = sb >= omni.Length ? omni.Length : (int)sb;
        int e = PowerOf2Exponent(Math.Max(LargestMagnitude(omni), LargestMagnitude(figureEight)));
        double den = 0, num = 0;
        for (int n = 0; n < nb; n++)
        {
            double o = Math.ScaleB(omni[n], -e);
            den += o * o;
            if (n >= na)
            {
                double f = Math.ScaleB(figureEight[n], -e);
                num += f * f;
            }
        }
        if (!(den > 0))
            throw new ArgumentException("omni must have energy before stop", nameof(omni));
        return num / den;
    }
}
