using System.Numerics;

namespace SignalForge;

/// <summary>Errors over a compared span.</summary>
/// <param name="Errors">Number of positions that differ.</param>
/// <param name="Compared">Number of positions compared.</param>
/// <param name="Rate">Errors / Compared; NaN when nothing was compared.</param>
public sealed record ErrorCount(int Errors, int Compared, double Rate);

/// <summary>Error vector magnitude, normalized to the mean power of the reference symbols.</summary>
/// <param name="Rms">√(Σ|measured − reference|² / Σ|reference|²).</param>
/// <param name="RmsPercent">100·Rms.</param>
/// <param name="RmsDb">20·log10(Rms); −∞ for a perfect match.</param>
/// <param name="Peak">Largest |measured − reference| over the RMS reference amplitude.</param>
/// <param name="PeakIndex">First index of the largest error.</param>
/// <param name="NumSymbols">Number of symbols compared.</param>
public sealed record Evm(double Rms, double RmsPercent, double RmsDb, double Peak, int PeakIndex, int NumSymbols);

/// <summary>Error-rate metrics, EVM and theoretical error rates.</summary>
public static class Metrics
{
    /// <summary>Count differing bits between two equal-length bit sequences.</summary>
    public static ErrorCount BitErrors(ReadOnlySpan<byte> reference, ReadOnlySpan<byte> received)
    {
        if (reference.Length != received.Length)
            throw new ArgumentException(
                $"length mismatch: {reference.Length} reference vs {received.Length} received", nameof(received));
        int errors = 0;
        for (int i = 0; i < reference.Length; i++)
            if (reference[i] != received[i])
                errors++;
        int n = reference.Length;
        return new ErrorCount(errors, n, n > 0 ? (double)errors / n : double.NaN);
    }

    /// <summary>RMS and peak EVM of measured symbols against reference symbols; see docs/conventions.md.</summary>
    public static Evm Evm(ReadOnlySpan<Complex> measured, ReadOnlySpan<Complex> reference)
    {
        if (measured.Length != reference.Length || measured.IsEmpty)
            throw new ArgumentException("measured and reference must be non-empty and the same length", nameof(measured));
        double refPower = 0, errPower = 0, peak = -1;
        int peakIndex = 0;
        for (int i = 0; i < measured.Length; i++)
        {
            Complex m = measured[i], r = reference[i];
            if (!double.IsFinite(m.Real) || !double.IsFinite(m.Imaginary) || !double.IsFinite(r.Real) || !double.IsFinite(r.Imaginary))
                throw new ArgumentException("symbols must be finite", nameof(measured));
            refPower += r.Real * r.Real + r.Imaginary * r.Imaginary;
            double e = Complex.Abs(m - r);
            errPower += e * e;
            if (e > peak)
                (peak, peakIndex) = (e, i);
        }
        if (!(refPower > 0))
            throw new ArgumentException("reference power must be positive", nameof(reference));
        double rms = Math.Sqrt(errPower / refPower);
        return new Evm(rms, 100 * rms, rms > 0 ? 20 * Math.Log10(rms) : double.NegativeInfinity,
            peak / Math.Sqrt(refPower / measured.Length), peakIndex, measured.Length);
    }

    /// <summary>Bit error rate of Gray-coded QPSK in AWGN: ½·erfc(√(Eb/N0)), Eb/N0 in dB.</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double QpskBerTheory(double ebN0Db) =>
        0.5 * SpecialFunctions.Erfc(Math.Sqrt(EbN0(ebN0Db)));

    /// <summary>Bit error rate of Gray QPSK in Rayleigh fading with a coherent receiver, mean Eb/N0 in
    /// dB: ½·(1 − √(γ/(1+γ))) (conventions: EVM and BER).</summary>
    /// <param name="ebN0Db">Mean Eb/N0 in dB, not NaN.</param>
    public static double QpskBerRayleighTheory(double ebN0Db)
    {
        double g = EbN0(ebN0Db);
        return double.IsInfinity(g) ? 0 : 1 / (2 * (1 + g) * (1 + Math.Sqrt(g / (1 + g))));
    }

    /// <summary>Exact bit error rate of Gray 16-QAM in AWGN (conventions: EVM and BER).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Qam16BerTheory(double ebN0Db)
    {
        double r = Math.Sqrt(2 * EbN0(ebN0Db) / 5);
        return (3 * SpecialFunctions.Erfc(r) + 2 * SpecialFunctions.Erfc(3 * r) - SpecialFunctions.Erfc(5 * r)) / 8;
    }

    /// <summary>Exact symbol error rate of 16-QAM in AWGN: p·(2 − p), p = ¾·erfc(r).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Qam16SerTheory(double ebN0Db)
    {
        double p = 0.75 * SpecialFunctions.Erfc(Math.Sqrt(2 * EbN0(ebN0Db) / 5));
        return p * (2 - p);
    }

    /// <summary>Exact bit error rate of Gray 64-QAM in AWGN (conventions: EVM and BER; ADR 0052).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Qam64BerTheory(double ebN0Db)
    {
        double r = Math.Sqrt(EbN0(ebN0Db) / 7);
        return (7 * SpecialFunctions.Erfc(r) + 6 * SpecialFunctions.Erfc(3 * r) - SpecialFunctions.Erfc(5 * r)
            + SpecialFunctions.Erfc(9 * r) - SpecialFunctions.Erfc(13 * r)) / 24;
    }

    /// <summary>Exact symbol error rate of 64-QAM in AWGN: p·(2 − p), p = ⅞·erfc(r).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Qam64SerTheory(double ebN0Db)
    {
        double p = 0.875 * SpecialFunctions.Erfc(Math.Sqrt(EbN0(ebN0Db) / 7));
        return p * (2 - p);
    }

    /// <summary>Exact symbol error rate of 8-PSK in AWGN: 2·T(π/8) (conventions: EVM and BER).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Psk8SerTheory(double ebN0Db) => 2 * PhaseTail(Math.PI / 8, 3 * EbN0(ebN0Db));

    /// <summary>Exact bit error rate of Gray 8-PSK in AWGN: ⅔·(T(π/8) + T(3π/8)).</summary>
    /// <param name="ebN0Db">Eb/N0 in dB, not NaN.</param>
    public static double Psk8BerTheory(double ebN0Db)
    {
        double esN0 = 3 * EbN0(ebN0Db);
        return 2.0 / 3 * (PhaseTail(Math.PI / 8, esN0) + PhaseTail(3 * Math.PI / 8, esN0));
    }

    private static double EbN0(double ebN0Db)
    {
        if (double.IsNaN(ebN0Db))
            throw new ArgumentOutOfRangeException(nameof(ebN0Db), ebN0Db, "must not be NaN");
        return Math.Pow(10, ebN0Db / 10);
    }

    private const int TailPanels = 4096;

    // P(received phase beyond psi on one side), Pawula's integral by Simpson's rule.
    private static double PhaseTail(double psi, double esN0)
    {
        double k = esN0 * Math.Sin(psi) * Math.Sin(psi);
        if (k == 0)
            return (Math.PI - psi) / (2 * Math.PI);
        if (double.IsPositiveInfinity(k))
            return 0;
        double h = (Math.PI - psi) / TailPanels;
        double total = 0;
        for (int i = 1; i < TailPanels; i++)
        {
            double s = Math.Sin(i * h);
            total += (i % 2 == 1 ? 4 : 2) * Math.Exp(-k / (s * s));
        }
        total += Math.Exp(-esN0); // the theta = 0 end is 0
        return total * h / 3 / (2 * Math.PI);
    }
}
