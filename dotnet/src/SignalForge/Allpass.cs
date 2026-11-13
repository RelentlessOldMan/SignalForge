namespace SignalForge;

public static partial class Dsp
{
    /// <summary>First-order all-pass section <c>[b0, b1, b2, a0, a1, a2]</c>, phase −π/2 at the
    /// cutoff (conventions: IIR filters, All-pass sections).</summary>
    /// <param name="cutoff">Frequency in Hz of the −π/2 phase, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] AllpassFirstOrder(double cutoff, double sampleRate)
    {
        double c = AllpassC(cutoff, Check.PositiveFinite(sampleRate, nameof(sampleRate)), nameof(cutoff));
        return Usable([[c, 1, 0, 1, c, 0]]);
    }

    /// <summary>Second-order all-pass section <c>[b0, b1, b2, a0, a1, a2]</c>, phase −π at the
    /// center and −π/2, −3π/2 at two frequencies bandwidth apart (conventions: IIR filters,
    /// All-pass sections).</summary>
    /// <param name="center">Frequency in Hz of the −π phase, between 0 and sampleRate/2.</param>
    /// <param name="bandwidth">Distance in Hz between the −π/2 and −3π/2 phases, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] AllpassSecondOrder(double center, double bandwidth, double sampleRate)
    {
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        double d = -Math.Cos(2 * Math.PI * BandEdge(center, fs, nameof(center)));
        double c = AllpassC(bandwidth, fs, nameof(bandwidth));
        return Usable([[-c, d * (1 - c), 1, 1, d * (1 - c), -c]]);
    }

    private static double AllpassC(double f, double fs, string name)
    {
        double t = Math.Tan(Math.PI * BandEdge(f, fs, name));
        return (t - 1) / (t + 1);
    }
}
