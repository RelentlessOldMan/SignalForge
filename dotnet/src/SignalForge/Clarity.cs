using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The clarity <c>10·log10(E_early/E_late)</c> with the boundary at
    /// <paramref name="time"/> seconds (C80 by default; conventions: Clarity and definition;
    /// ADR 0172).</summary>
    /// <param name="impulseResponse">Complex response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="time">The early/late boundary in seconds, finite and positive.</param>
    /// <returns>The clarity in dB; <c>+∞</c> with no late energy, <c>−∞</c> with no early.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Clarity(ReadOnlySpan<Complex> impulseResponse, double sampleRate, double time = 0.08) =>
        ClarityDb(EarlyLate(ResponsePowers(impulseResponse), sampleRate, time));

    /// <summary>The clarity <c>10·log10(E_early/E_late)</c> with the boundary at
    /// <paramref name="time"/> seconds (C80 by default; conventions: Clarity and definition;
    /// ADR 0172).</summary>
    /// <param name="impulseResponse">Real response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="time">The early/late boundary in seconds, finite and positive.</param>
    /// <returns>The clarity in dB; <c>+∞</c> with no late energy, <c>−∞</c> with no early.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Clarity(ReadOnlySpan<double> impulseResponse, double sampleRate, double time = 0.08) =>
        ClarityDb(EarlyLate(ResponsePowers(impulseResponse), sampleRate, time));

    /// <summary>The definition <c>E_early/E_total</c> with the boundary at
    /// <paramref name="time"/> seconds (D50 by default; conventions: Clarity and definition;
    /// ADR 0172).</summary>
    /// <param name="impulseResponse">Complex response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="time">The early/late boundary in seconds, finite and positive.</param>
    /// <returns>The early fraction of the energy, in [0, 1].</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Definition(ReadOnlySpan<Complex> impulseResponse, double sampleRate, double time = 0.05) =>
        EarlyFraction(EarlyLate(ResponsePowers(impulseResponse), sampleRate, time));

    /// <summary>The definition <c>E_early/E_total</c> with the boundary at
    /// <paramref name="time"/> seconds (D50 by default; conventions: Clarity and definition;
    /// ADR 0172).</summary>
    /// <param name="impulseResponse">Real response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="time">The early/late boundary in seconds, finite and positive.</param>
    /// <returns>The early fraction of the energy, in [0, 1].</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Definition(ReadOnlySpan<double> impulseResponse, double sampleRate, double time = 0.05) =>
        EarlyFraction(EarlyLate(ResponsePowers(impulseResponse), sampleRate, time));

    /// <summary>The centre time <c>Σ (n/fs)·|h[n]|² / Σ |h[n]|²</c> in seconds, from index 0
    /// (conventions: Centre time; ADR 0173).</summary>
    /// <param name="impulseResponse">Complex response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The centre time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CentreTime(ReadOnlySpan<Complex> impulseResponse, double sampleRate) =>
        EnergyCentre(ResponsePowers(impulseResponse), sampleRate);

    /// <summary>The centre time <c>Σ (n/fs)·h[n]² / Σ h[n]²</c> in seconds, from index 0
    /// (conventions: Centre time; ADR 0173).</summary>
    /// <param name="impulseResponse">Real response from index 0, finite, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The centre time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CentreTime(ReadOnlySpan<double> impulseResponse, double sampleRate) =>
        EnergyCentre(ResponsePowers(impulseResponse), sampleRate);

    private static double EnergyCentre(double[] p, double sampleRate)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        double total = 0, moment = 0;
        for (int n = 0; n < p.Length; n++)
        {
            total += p[n];
            moment += n * p[n];
        }
        if (!(total > 0))
            throw new ArgumentException("impulseResponse must not be all zero", nameof(p));
        return moment / total / sampleRate;
    }

    private static double[] ResponsePowers(ReadOnlySpan<Complex> impulseResponse) =>
        ResponsePowers(impulseResponse, PowerOf2Exponent(LargestMagnitude(impulseResponse)));

    private static double[] ResponsePowers(ReadOnlySpan<Complex> impulseResponse, int exponent)
    {
        if (impulseResponse.IsEmpty)
            throw new ArgumentException("impulseResponse must not be empty", nameof(impulseResponse));
        var p = new double[impulseResponse.Length];
        for (int n = 0; n < p.Length; n++)
        {
            Complex v = impulseResponse[n];
            if (!(double.IsFinite(v.Real) && double.IsFinite(v.Imaginary)))
                throw new ArgumentException("impulseResponse must be finite", nameof(impulseResponse));
            double re = Math.ScaleB(v.Real, -exponent), im = Math.ScaleB(v.Imaginary, -exponent);
            p[n] = re * re + im * im;
        }
        return p;
    }

    private static double[] ResponsePowers(ReadOnlySpan<double> impulseResponse) =>
        ResponsePowers(impulseResponse, PowerOf2Exponent(LargestMagnitude(impulseResponse)));

    private static double[] ResponsePowers(ReadOnlySpan<double> impulseResponse, int exponent)
    {
        if (impulseResponse.IsEmpty)
            throw new ArgumentException("impulseResponse must not be empty", nameof(impulseResponse));
        var p = new double[impulseResponse.Length];
        for (int n = 0; n < p.Length; n++)
        {
            if (!double.IsFinite(impulseResponse[n]))
                throw new ArgumentException("impulseResponse must be finite", nameof(impulseResponse));
            double v = Math.ScaleB(impulseResponse[n], -exponent);
            p[n] = v * v;
        }
        return p;
    }

    private static (double Early, double Late) EarlyLate(double[] p, double sampleRate, double time)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (!(double.IsFinite(time) && time > 0))
            throw new ArgumentOutOfRangeException(nameof(time), time, "must be finite and positive");
        double size = Math.Floor(time * sampleRate + 0.5);
        if (size < 1)
            throw new ArgumentOutOfRangeException(nameof(time), time, "time * sampleRate must round to at least 1 sample");
        int boundary = size >= p.Length ? p.Length : (int)size;
        double early = 0, late = 0;
        for (int n = 0; n < p.Length; n++)
        {
            if (n < boundary)
                early += p[n];
            else
                late += p[n];
        }
        if (!(early + late > 0))
            throw new ArgumentException("impulseResponse must not be all zero", nameof(p));
        return (early, late);
    }

    private static double ClarityDb((double Early, double Late) e) =>
        e.Late == 0 ? double.PositiveInfinity : e.Early == 0 ? double.NegativeInfinity : 10 * Math.Log10(e.Early / e.Late);

    private static double EarlyFraction((double Early, double Late) e) => e.Early / (e.Early + e.Late);
}
