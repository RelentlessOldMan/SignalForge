namespace SignalForge;

public static partial class Dsp
{
    /// <summary>The IEC 61672-1 A-weighting filter by the bilinear transform, three second-order
    /// sections <c>[b0, b1, b2, a0, a1, a2]</c>, 0 dB at 1 kHz (conventions: Weighting filters;
    /// ADR 0165).</summary>
    /// <param name="sampleRate">Sample rate in Hz, finite and above 2000.</param>
    /// <returns>The sections.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] AWeightingSos(double sampleRate) =>
        WeightingSos(sampleRate,
        [
            [(true, Units.WeightF1), (true, Units.WeightF1)],
            [(true, Units.WeightF2), (true, Units.WeightF3)],
            [(false, Units.WeightF4), (false, Units.WeightF4)],
        ]);

    /// <summary>The IEC 61672-1 C-weighting filter by the bilinear transform, two second-order
    /// sections <c>[b0, b1, b2, a0, a1, a2]</c>, 0 dB at 1 kHz (conventions: Weighting filters;
    /// ADR 0165).</summary>
    /// <param name="sampleRate">Sample rate in Hz, finite and above 2000.</param>
    /// <returns>The sections.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] CWeightingSos(double sampleRate) =>
        WeightingSos(sampleRate,
        [
            [(true, Units.WeightF1), (true, Units.WeightF1)],
            [(false, Units.WeightF4), (false, Units.WeightF4)],
        ]);

    private static double[][] WeightingSos(double sampleRate, (bool High, double Hz)[][] sections)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 2000))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and above 2000 Hz");
        double k = 2 * sampleRate;
        double bigOmega = k * Math.Tan(Math.PI * 1000 / sampleRate);
        double magnitude = 1;
        var rows = new double[sections.Length][];
        for (int i = 0; i < sections.Length; i++)
        {
            var factors = new (double B0, double B1, double A1)[2];
            for (int j = 0; j < 2; j++)
            {
                (bool high, double hz) = sections[i][j];
                double w = 2 * Math.PI * hz, d = k + w;
                factors[j] = high ? (k / d, -k / d, (w - k) / d) : (w / d, w / d, (w - k) / d);
                magnitude *= (high ? bigOmega : w) / double.Hypot(bigOmega, w);
            }
            var (p, q) = (factors[0], factors[1]);
            rows[i] = [p.B0 * q.B0, p.B0 * q.B1 + p.B1 * q.B0, p.B1 * q.B1, 1, p.A1 + q.A1, p.A1 * q.A1];
        }
        for (int c = 0; c < 3; c++)
            rows[0][c] /= magnitude;
        return Usable([.. rows]);
    }
}
