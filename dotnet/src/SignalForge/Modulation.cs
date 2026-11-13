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

    private static readonly double InvSqrt10 = 1.0 / Math.Sqrt(10.0);
    private static readonly double Qam16Threshold = 2.0 / Math.Sqrt(10.0);

    private static int Label(ReadOnlySpan<byte> bits, int start, int k)
    {
        int m = 0;
        for (int i = 0; i < k; i++)
        {
            byte b = bits[start + i];
            if (b > 1)
                throw new ArgumentException("bits must be 0 or 1", nameof(bits));
            m = 2 * m + b;
        }
        return m;
    }

    private static void CheckLength(ReadOnlySpan<byte> bits, int k, string name)
    {
        if (bits.Length % k != 0)
            throw new ArgumentException($"{name} needs a multiple of {k} bits", nameof(bits));
    }

    /// <summary>Gray-coded 8-PSK: label m (3 bits, MSB first) to e^{jπp/4} where p ⊕ (p &gt;&gt; 1) = m
    /// (conventions: Bits and symbols).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of 3.</param>
    public static Complex[] Psk8Map(ReadOnlySpan<byte> bits)
    {
        CheckLength(bits, 3, "8-PSK");
        var symbols = new Complex[bits.Length / 3];
        for (int s = 0; s < symbols.Length; s++)
        {
            int m = Label(bits, 3 * s, 3);
            int p = m ^ (m >> 1) ^ (m >> 2);
            symbols[s] = Complex.FromPolarCoordinates(1, Math.PI / 4 * p);
        }
        return symbols;
    }

    /// <summary>Hard-decision 8-PSK: the nearest point's label; 0 decides 000.</summary>
    /// <param name="symbols">Received symbols.</param>
    public static byte[] Psk8DemapHard(ReadOnlySpan<Complex> symbols)
    {
        var bits = new byte[3 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            double sector = Math.Floor(Math.Atan2(symbols[s].Imaginary, symbols[s].Real) / (Math.PI / 4) + 0.5);
            int p = (((int)sector % 8) + 8) % 8;
            int m = p ^ (p >> 1);
            for (int i = 0; i < 3; i++)
                bits[3 * s + i] = (byte)((m >> (2 - i)) & 1);
        }
        return bits;
    }

    /// <summary>Gray-coded 16-QAM: I from (b0, b1), Q from (b2, b3), each (1 − 2·first)·(3 − 2·second),
    /// over √10 (conventions: Bits and symbols).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of 4.</param>
    public static Complex[] Qam16Map(ReadOnlySpan<byte> bits)
    {
        CheckLength(bits, 4, "16-QAM");
        var symbols = new Complex[bits.Length / 4];
        for (int s = 0; s < symbols.Length; s++)
        {
            int m = Label(bits, 4 * s, 4);
            double i = (1 - 2 * ((m >> 3) & 1)) * (3 - 2 * ((m >> 2) & 1));
            double q = (1 - 2 * ((m >> 1) & 1)) * (3 - 2 * (m & 1));
            symbols[s] = new Complex(i * InvSqrt10, q * InvSqrt10);
        }
        return symbols;
    }

    /// <summary>Hard-decision 16-QAM: per component v, first bit v &lt; 0, second |v| &lt; 2/√10.</summary>
    /// <param name="symbols">Received symbols.</param>
    public static byte[] Qam16DemapHard(ReadOnlySpan<Complex> symbols)
    {
        var bits = new byte[4 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            double i = symbols[s].Real, q = symbols[s].Imaginary;
            bits[4 * s] = i < 0 ? (byte)1 : (byte)0;
            bits[4 * s + 1] = Math.Abs(i) < Qam16Threshold ? (byte)1 : (byte)0;
            bits[4 * s + 2] = q < 0 ? (byte)1 : (byte)0;
            bits[4 * s + 3] = Math.Abs(q) < Qam16Threshold ? (byte)1 : (byte)0;
        }
        return bits;
    }
}
