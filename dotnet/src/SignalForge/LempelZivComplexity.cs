namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The LZ76 phrase count of a 0/1 sequence, by the Kaspar-Schuster scan
    /// (conventions: Lempel-Ziv complexity; ADR 0336).</summary>
    /// <param name="bits">Bits, each 0 or 1, at least one.</param>
    /// <returns>The number of phrases.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static int LempelZivComplexity(ReadOnlySpan<byte> bits)
    {
        int n = bits.Length;
        if (n < 1)
            throw new ArgumentException("needs at least one bit", nameof(bits));
        foreach (byte v in bits)
        {
            if (v > 1)
                throw new ArgumentException("bits must be 0 or 1", nameof(bits));
        }
        if (n == 1)
            return 1;
        int i = 0, k = 1, start = 1, kMax = 1, phrases = 1;
        while (true)
        {
            if (bits[i + k - 1] == bits[start + k - 1])
            {
                k++;
                if (start + k > n)
                    return phrases + 1;
            }
            else
            {
                kMax = Math.Max(kMax, k);
                i++;
                if (i == start)
                {
                    phrases++;
                    start += kMax;
                    if (start + 1 > n)
                        return phrases;
                    i = 0;
                    k = 1;
                    kMax = 1;
                }
                else
                {
                    k = 1;
                }
            }
        }
    }
}
