using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The stage support <c>ST_early</c> (20–100 ms) or <c>ST_late</c> (100–1000 ms)
    /// against the direct 0–10 ms, in dB (conventions: Stage support; ADR 0179).</summary>
    /// <param name="impulseResponse">Complex response from the direct sound at index 0, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive, at least 50.</param>
    /// <param name="late">True for <c>ST_late</c>, false for <c>ST_early</c>.</param>
    /// <returns>The stage support in dB; <c>−∞</c> for a silent window.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double StageSupport(ReadOnlySpan<Complex> impulseResponse, double sampleRate, bool late = false) =>
        Support(ResponsePowers(impulseResponse), sampleRate, late);

    /// <summary>The stage support <c>ST_early</c> (20–100 ms) or <c>ST_late</c> (100–1000 ms)
    /// against the direct 0–10 ms, in dB (conventions: Stage support; ADR 0179).</summary>
    /// <param name="impulseResponse">Real response from the direct sound at index 0, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive, at least 50.</param>
    /// <param name="late">True for <c>ST_late</c>, false for <c>ST_early</c>.</param>
    /// <returns>The stage support in dB; <c>−∞</c> for a silent window.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double StageSupport(ReadOnlySpan<double> impulseResponse, double sampleRate, bool late = false) =>
        Support(ResponsePowers(impulseResponse), sampleRate, late);

    private static double Support(double[] p, double sampleRate, bool late)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        int directEnd = SupportBound(0.01, sampleRate, p.Length);
        if (directEnd < 1)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must give at least one direct-sound sample");
        double direct = WindowEnergy(p, 0, directEnd);
        if (!(direct > 0))
            throw new ArgumentException("impulseResponse must have energy in the direct sound");
        double window = late
            ? WindowEnergy(p, SupportBound(0.1, sampleRate, p.Length), SupportBound(1.0, sampleRate, p.Length))
            : WindowEnergy(p, SupportBound(0.02, sampleRate, p.Length), SupportBound(0.1, sampleRate, p.Length));
        return window == 0 ? double.NegativeInfinity : 10 * Math.Log10(window / direct);
    }

    private static int SupportBound(double t, double sampleRate, int length)
    {
        double n = Math.Floor(t * sampleRate + 0.5);
        return n >= length ? length : (int)n;
    }

    private static double WindowEnergy(double[] p, int start, int stop)
    {
        double e = 0;
        for (int n = start; n < stop; n++)
            e += p[n];
        return e;
    }
}
