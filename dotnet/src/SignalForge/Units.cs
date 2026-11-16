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
