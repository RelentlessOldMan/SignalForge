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

    private static double NonNegative(double x, string name) =>
        x >= 0 ? x : throw new ArgumentOutOfRangeException(name, x, "must be non-negative");

    private static double Positive(double x, string name) =>
        Check.PositiveFinite(x, name);
}
