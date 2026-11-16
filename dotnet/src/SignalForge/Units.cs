namespace SignalForge;

/// <summary>Unit conversions: dB, dBm, voltage and power. Definitions in docs/conventions.md.</summary>
public static class Units
{
    /// <summary>Default reference impedance in ohms.</summary>
    public const double DefaultImpedance = 50.0;

    /// <summary>Power ratio to dB: 10·log10(ratio). Zero gives −∞; negative or NaN throws.</summary>
    public static double LinToDb(double ratio) => 10.0 * Math.Log10(NonNegative(ratio, nameof(ratio)));

    /// <summary>dB to power ratio: 10^(dB/10).</summary>
    public static double DbToLin(double db) => Math.Pow(10.0, db / 10.0);

    /// <summary>Amplitude ratio to dB: 20·log10(ratio). Zero gives −∞; negative or NaN throws.</summary>
    public static double AmpToDb(double ratio) => 20.0 * Math.Log10(NonNegative(ratio, nameof(ratio)));

    /// <summary>dB to amplitude ratio: 10^(dB/20).</summary>
    public static double DbToAmp(double db) => Math.Pow(10.0, db / 20.0);

    /// <summary>Power in watts to dBm.</summary>
    public static double WToDbm(double watts) => 10.0 * Math.Log10(NonNegative(watts, nameof(watts)) / 1e-3);

    /// <summary>Power in dBm to watts.</summary>
    public static double DbmToW(double dbm) => 1e-3 * Math.Pow(10.0, dbm / 10.0);

    /// <summary>RMS voltage across <paramref name="impedance"/> ohms to dBm (P = Vrms² / R).</summary>
    public static double VrmsToDbm(double vrms, double impedance = DefaultImpedance)
    {
        double r = Positive(impedance, nameof(impedance));
        double v = NonNegative(vrms, nameof(vrms));
        return 10.0 * Math.Log10(v * v / r / 1e-3);
    }

    /// <summary>Power in dBm to RMS voltage across <paramref name="impedance"/> ohms.</summary>
    public static double DbmToVrms(double dbm, double impedance = DefaultImpedance)
    {
        double r = Positive(impedance, nameof(impedance));
        return Math.Sqrt(1e-3 * Math.Pow(10.0, dbm / 10.0) * r);
    }

    /// <summary>Frequency in Hz to mel: HTK <c>2595·log10(1 + f/700)</c>, or Slaney, linear below
    /// 1 kHz and logarithmic above (conventions: Mel scale; ADR 0154).</summary>
    /// <param name="hz">A frequency, finite and non-negative.</param>
    /// <param name="scale">Which mel definition.</param>
    /// <returns>The mel value.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HzToMel(double hz, MelScale scale = MelScale.Htk)
    {
        FiniteNonNegative(hz, nameof(hz));
        return scale switch
        {
            MelScale.Htk => 2595.0 * Math.Log10(1.0 + hz / 700.0),
            MelScale.Slaney => hz >= 1000.0 ? 15.0 + Math.Log(hz / 1000.0) / SlaneyLogStep : hz / SlaneyHzPerMel,
            _ => throw new ArgumentOutOfRangeException(nameof(scale), scale, "unknown mel scale"),
        };
    }

    /// <summary>Mel to frequency in Hz, the inverse of <see cref="HzToMel"/> (conventions: Mel
    /// scale; ADR 0154).</summary>
    /// <param name="mel">A mel value, finite and non-negative.</param>
    /// <param name="scale">Which mel definition.</param>
    /// <returns>The frequency in Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MelToHz(double mel, MelScale scale = MelScale.Htk)
    {
        FiniteNonNegative(mel, nameof(mel));
        return scale switch
        {
            MelScale.Htk => 700.0 * (Math.Pow(10.0, mel / 2595.0) - 1.0),
            MelScale.Slaney => mel >= 15.0 ? 1000.0 * Math.Exp((mel - 15.0) * SlaneyLogStep) : mel * SlaneyHzPerMel,
            _ => throw new ArgumentOutOfRangeException(nameof(scale), scale, "unknown mel scale"),
        };
    }

    /// <summary>Frequency in Hz to ERB number, <c>21.4·log10(4.37 f/1000 + 1)</c> (conventions:
    /// ERB scale; ADR 0160).</summary>
    /// <param name="hz">A frequency, finite and non-negative.</param>
    /// <returns>The ERB number.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HzToErbRate(double hz)
    {
        FiniteNonNegative(hz, nameof(hz));
        return 21.4 * Math.Log10(4.37 * hz / 1000.0 + 1.0);
    }

    /// <summary>ERB number to frequency in Hz, the inverse of <see cref="HzToErbRate"/>
    /// (conventions: ERB scale; ADR 0160).</summary>
    /// <param name="erb">An ERB number, finite and non-negative.</param>
    /// <returns>The frequency in Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ErbRateToHz(double erb)
    {
        FiniteNonNegative(erb, nameof(erb));
        return (Math.Pow(10.0, erb / 21.4) - 1.0) * 1000.0 / 4.37;
    }

    /// <summary>The auditory filter's equivalent rectangular bandwidth in Hz,
    /// <c>24.7·(4.37 f/1000 + 1)</c> (conventions: ERB scale; ADR 0160).</summary>
    /// <param name="hz">A frequency, finite and non-negative.</param>
    /// <returns>The bandwidth in Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ErbBandwidth(double hz)
    {
        FiniteNonNegative(hz, nameof(hz));
        return 24.7 * (4.37 * hz / 1000.0 + 1.0);
    }

    /// <summary>Frequencies equally spaced in ERB rate from <paramref name="minFrequency"/> to
    /// <paramref name="maxFrequency"/>, both included, ascending (conventions: ERB-spaced
    /// frequencies; ADR 0162).</summary>
    /// <param name="minFrequency">The lowest frequency in Hz, at least 0.</param>
    /// <param name="maxFrequency">The highest frequency in Hz, above the lowest, finite.</param>
    /// <param name="nFrequencies">How many frequencies, at least 1.</param>
    /// <returns>The frequencies in Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ErbSpace(double minFrequency, double maxFrequency, int nFrequencies)
    {
        if (!(double.IsFinite(minFrequency) && double.IsFinite(maxFrequency) && minFrequency >= 0 && minFrequency < maxFrequency))
            throw new ArgumentException("need 0 <= minFrequency < maxFrequency, both finite", nameof(maxFrequency));
        if (nFrequencies < 1)
            throw new ArgumentOutOfRangeException(nameof(nFrequencies), "nFrequencies must be at least 1");
        if (nFrequencies == 1)
            return [minFrequency];
        double eLo = HzToErbRate(minFrequency), eHi = HzToErbRate(maxFrequency);
        var result = new double[nFrequencies];
        for (int i = 0; i < nFrequencies; i++)
            result[i] = ErbRateToHz(eLo + (eHi - eLo) * i / (nFrequencies - 1));
        result[0] = minFrequency;
        result[^1] = maxFrequency;
        return result;
    }

    /// <summary>Frequency in Hz to Bark, Traunmüller (1990) with both corrections (conventions:
    /// Bark scale; ADR 0163).</summary>
    /// <param name="hz">A frequency, finite and non-negative.</param>
    /// <returns>The critical-band rate in Bark.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HzToBark(double hz)
    {
        FiniteNonNegative(hz, nameof(hz));
        double z = 26.81 * hz / (1960.0 + hz) - 0.53;
        return z < 2.0 ? z + 0.15 * (2.0 - z) : z > 20.1 ? z + 0.22 * (z - 20.1) : z;
    }

    /// <summary>Bark to frequency in Hz, the inverse of <see cref="HzToBark"/> (conventions: Bark
    /// scale; ADR 0163).</summary>
    /// <param name="bark">A Bark value, finite, at least <c>HzToBark(0)</c> and below 27.6396.</param>
    /// <returns>The frequency in Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BarkToHz(double bark)
    {
        if (!(double.IsFinite(bark) && bark >= BarkAtZero))
            throw new ArgumentOutOfRangeException(nameof(bark), bark, "must be finite and at least HzToBark(0)");
        double z = bark < 2.0 ? (bark - 0.3) / 0.85 : bark > 20.1 ? (bark + 4.422) / 1.22 : bark;
        if (!(z < 26.28))
            throw new ArgumentOutOfRangeException(nameof(bark), bark, "must be below the limit 27.6396");
        return Math.Max(0.0, 1960.0 * (z + 0.53) / (26.28 - z));
    }

    /// <summary>The IEC 61672-1 A-weighting in dB, 0 at 1 kHz (conventions: Frequency
    /// weightings; ADR 0164).</summary>
    /// <param name="frequency">A frequency in Hz, finite and non-negative.</param>
    /// <returns>The weighting in dB; negative infinity at 0 Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double AWeighting(double frequency)
    {
        FiniteNonNegative(frequency, nameof(frequency));
        return ARaw(frequency) - A1000;
    }

    /// <summary>The IEC 61672-1 C-weighting in dB, 0 at 1 kHz (conventions: Frequency
    /// weightings; ADR 0164).</summary>
    /// <param name="frequency">A frequency in Hz, finite and non-negative.</param>
    /// <returns>The weighting in dB; negative infinity at 0 Hz.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CWeighting(double frequency)
    {
        FiniteNonNegative(frequency, nameof(frequency));
        return CRaw(frequency) - C1000;
    }

    /// <summary>IEC 61260-1 base-10 fractional-octave bands with mid-band frequencies in
    /// [<paramref name="minFrequency"/>, <paramref name="maxFrequency"/>], as rows
    /// <c>[lower, center, upper]</c> (conventions: Fractional-octave bands; ADR 0167).</summary>
    /// <param name="fraction">Bands per octave <c>b</c>, at least 1.</param>
    /// <param name="minFrequency">The lowest mid-band frequency in Hz, positive and finite.</param>
    /// <param name="maxFrequency">The highest mid-band frequency in Hz, at least the lowest, finite.</param>
    /// <returns>The bands, ascending; empty if none qualifies.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[][] OctaveBands(int fraction, double minFrequency, double maxFrequency)
    {
        if (fraction < 1)
            throw new ArgumentOutOfRangeException(nameof(fraction), fraction, "must be at least 1");
        if (!(double.IsFinite(minFrequency) && double.IsFinite(maxFrequency) && minFrequency > 0 && minFrequency <= maxFrequency))
            throw new ArgumentException("need 0 < minFrequency <= maxFrequency, both finite", nameof(maxFrequency));
        double shift = fraction % 2 == 0 ? 0.5 : 0.0;
        long first = (long)Math.Floor(fraction * 10.0 / 3 * Math.Log10(minFrequency / 1000) - shift) - 1;
        long last = (long)Math.Ceiling(fraction * 10.0 / 3 * Math.Log10(maxFrequency / 1000) - shift) + 1;
        double half = Math.Pow(10, 3.0 / (20.0 * fraction));
        var rows = new List<double[]>();
        for (long x = first; x <= last; x++)
        {
            double center = 1000 * Math.Pow(10, 3 * (x + shift) / (10.0 * fraction));
            if (minFrequency <= center && center <= maxFrequency)
                rows.Add([center / half, center, center * half]);
        }
        return [.. rows];
    }

    internal const double WeightF1 = 20.598997, WeightF2 = 107.65265, WeightF3 = 737.86223, WeightF4 = 12194.217;

    private static double ARaw(double f) =>
        40.0 * Math.Log10(WeightF4) + 80.0 * Math.Log10(f)
        - 40.0 * Math.Log10(double.Hypot(f, WeightF1)) - 20.0 * Math.Log10(double.Hypot(f, WeightF2))
        - 20.0 * Math.Log10(double.Hypot(f, WeightF3)) - 40.0 * Math.Log10(double.Hypot(f, WeightF4));

    private static double CRaw(double f) =>
        40.0 * Math.Log10(WeightF4) + 40.0 * Math.Log10(f)
        - 40.0 * Math.Log10(double.Hypot(f, WeightF1)) - 40.0 * Math.Log10(double.Hypot(f, WeightF4));

    private static readonly double A1000 = ARaw(1000.0);
    private static readonly double C1000 = CRaw(1000.0);

    private const double BarkAtZero = -0.53 + 0.15 * (2.0 - -0.53);

    private const double SlaneyHzPerMel = 200.0 / 3.0;
    private static readonly double SlaneyLogStep = Math.Log(6.4) / 27.0;

    private static void FiniteNonNegative(double x, string name)
    {
        if (!(double.IsFinite(x) && x >= 0))
            throw new ArgumentOutOfRangeException(name, x, "must be finite and non-negative");
    }

    private static double NonNegative(double x, string name) =>
        x >= 0 ? x : throw new ArgumentOutOfRangeException(name, x, "must be non-negative");

    private static double Positive(double x, string name) =>
        Check.PositiveFinite(x, name);
}

/// <summary>Which mel scale (conventions: Mel scale; ADR 0154).</summary>
public enum MelScale
{
    /// <summary>HTK: <c>2595·log10(1 + f/700)</c>.</summary>
    Htk,

    /// <summary>Slaney: linear at 200/3 Hz per mel to 1 kHz (15 mel), then 27 mel per factor of 6.4.</summary>
    Slaney,
}
