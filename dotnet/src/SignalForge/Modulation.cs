using System.Numerics;

namespace SignalForge;

/// <summary>Symbol mapping. Definitions in docs/conventions.md.</summary>
public static class Modulation
{
    private static readonly double InvSqrt2 = 1.0 / Math.Sqrt(2.0);

    /// <summary>Gray-coded QPSK: bit pair (b0, b1) to ((1−2·b0) + j·(1−2·b1)) / √2.</summary>
    public static Complex[] QpskMap(ReadOnlySpan<byte> bits)
    {
        if (bits.Length % 2 != 0)
            throw new ArgumentException("QPSK needs an even number of bits", nameof(bits));
        var symbols = new Complex[bits.Length / 2];
        for (int s = 0; s < symbols.Length; s++)
        {
            byte b0 = bits[2 * s], b1 = bits[2 * s + 1];
            if (b0 > 1 || b1 > 1)
                throw new ArgumentException("bits must be 0 or 1", nameof(bits));
            symbols[s] = new Complex((1.0 - 2.0 * b0) * InvSqrt2, (1.0 - 2.0 * b1) * InvSqrt2);
        }
        return symbols;
    }

    /// <summary>Hard-decision QPSK demapping: bit is 1 where I (or Q) is negative; exactly 0 gives 0.</summary>
    public static byte[] QpskDemapHard(ReadOnlySpan<Complex> symbols)
    {
        var bits = new byte[2 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            bits[2 * s] = symbols[s].Real < 0 ? (byte)1 : (byte)0;
            bits[2 * s + 1] = symbols[s].Imaginary < 0 ? (byte)1 : (byte)0;
        }
        return bits;
    }
}
