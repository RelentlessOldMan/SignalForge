namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Peaking EQ section: gain <paramref name="gainDb"/> at
    /// <paramref name="frequency"/>, unity at DC and fs/2 (conventions: Shelving and peaking EQ; ADR 0282).</summary>
    /// <param name="frequency">The corner or centre, Hz, above 0 and below half the sample
    /// rate.</param>
    /// <param name="gainDb">The shelf or peak gain, dB, finite.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One second-order section <c>[b0, b1, b2, 1, a1, a2]</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] PeakingEq(double frequency, double gainDb, double q, double sampleRate)
    {
        (double a, double c, double al, _) = EqTerms(frequency, gainDb, q, sampleRate);
        return EqSection(1 + al * a, -2 * c, 1 - al * a, 1 + al / a, -2 * c, 1 - al / a);
    }

    /// <summary>Low-shelf EQ section: gain <paramref name="gainDb"/> at DC, unity at fs/2 (conventions: Shelving and peaking EQ; ADR 0282).</summary>
    /// <param name="frequency">The corner or centre, Hz, above 0 and below half the sample
    /// rate.</param>
    /// <param name="gainDb">The shelf or peak gain, dB, finite.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One second-order section <c>[b0, b1, b2, 1, a1, a2]</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] LowShelf(double frequency, double gainDb, double q, double sampleRate)
    {
        (double a, double c, double al, double sa) = EqTerms(frequency, gainDb, q, sampleRate);
        return EqSection(
            a * ((a + 1) - (a - 1) * c + 2 * sa * al),
            2 * a * ((a - 1) - (a + 1) * c),
            a * ((a + 1) - (a - 1) * c - 2 * sa * al),
            (a + 1) + (a - 1) * c + 2 * sa * al,
            -2 * ((a - 1) + (a + 1) * c),
            (a + 1) + (a - 1) * c - 2 * sa * al);
    }

    /// <summary>High-shelf EQ section: unity at DC, gain <paramref name="gainDb"/> at fs/2 (conventions: Shelving and peaking EQ; ADR 0282).</summary>
    /// <param name="frequency">The corner or centre, Hz, above 0 and below half the sample
    /// rate.</param>
    /// <param name="gainDb">The shelf or peak gain, dB, finite.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One second-order section <c>[b0, b1, b2, 1, a1, a2]</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] HighShelf(double frequency, double gainDb, double q, double sampleRate)
    {
        (double a, double c, double al, double sa) = EqTerms(frequency, gainDb, q, sampleRate);
        return EqSection(
            a * ((a + 1) + (a - 1) * c + 2 * sa * al),
            -2 * a * ((a - 1) + (a + 1) * c),
            a * ((a + 1) + (a - 1) * c - 2 * sa * al),
            (a + 1) - (a - 1) * c + 2 * sa * al,
            2 * ((a - 1) - (a + 1) * c),
            (a + 1) - (a - 1) * c - 2 * sa * al);
    }

    private static (double A, double C, double Alpha, double SqrtA) EqTerms(double frequency, double gainDb, double q, double sampleRate)
    {
        if (!double.IsFinite(sampleRate) || sampleRate <= 0)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sampleRate must be positive");
        if (!double.IsFinite(frequency) || !(frequency > 0 && frequency < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must be in (0, sampleRate / 2)");
        if (!double.IsFinite(gainDb))
            throw new ArgumentOutOfRangeException(nameof(gainDb), "gainDb must be finite");
        if (!double.IsFinite(q) || !(q > 0))
            throw new ArgumentOutOfRangeException(nameof(q), "q must be positive");
        double a = Math.Pow(10, gainDb / 40);
        double w0 = 2 * Math.PI * frequency / sampleRate;
        return (a, Math.Cos(w0), Math.Sin(w0) / (2 * q), Math.Sqrt(a));
    }

    private static double[][] EqSection(double b0, double b1, double b2, double a0, double a1, double a2) =>
        Usable([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]]);

    /// <summary>Tilt EQ section: <c>−gainDb/2</c> at DC, <c>+gainDb/2</c> at fs/2, unity at
    /// <paramref name="frequency"/> (conventions: Tilt EQ; ADR 0283).</summary>
    /// <param name="frequency">The pivot, Hz, above 0 and below half the sample rate.</param>
    /// <param name="gainDb">The tilt, dB from DC to fs/2, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One section <c>[b0, b1, 0, 1, a1, 0]</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] TiltEq(double frequency, double gainDb, double sampleRate)
    {
        if (!double.IsFinite(sampleRate) || sampleRate <= 0)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sampleRate must be positive");
        if (!double.IsFinite(frequency) || !(frequency > 0 && frequency < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must be in (0, sampleRate / 2)");
        if (!double.IsFinite(gainDb))
            throw new ArgumentOutOfRangeException(nameof(gainDb), "gainDb must be finite");
        double bigT = Math.Pow(10, gainDb / 40);
        double t = Math.Tan(Math.PI * frequency / sampleRate);
        double d = 1 + bigT * t;
        return Usable([[(bigT + t) / d, (t - bigT) / d, 0.0, 1.0, (bigT * t - 1) / d, 0.0]]);
    }
}
