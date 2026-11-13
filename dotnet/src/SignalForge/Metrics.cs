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
    public static double QpskBerTheory(double ebN0Db)
    {
        if (double.IsNaN(ebN0Db))
            throw new ArgumentOutOfRangeException(nameof(ebN0Db), ebN0Db, "must not be NaN");
        return 0.5 * SpecialFunctions.Erfc(Math.Sqrt(Math.Pow(10, ebN0Db / 10)));
    }
}
