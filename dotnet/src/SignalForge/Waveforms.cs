using System.Numerics;

namespace SignalForge;

/// <summary>Waveform generators: tones and PRBS. Definitions in docs/conventions.md.</summary>
public static class Waveforms
{
    /// <summary>ITU-T O.150 PRBS polynomials xᵐ + xᵏ + 1 as order → k.</summary>
    public static IReadOnlyDictionary<int, int> PrbsTaps { get; } = new Dictionary<int, int>
    {
        [7] = 6,
        [9] = 5,
        [11] = 9,
        [15] = 14,
        [20] = 3,
        [23] = 18,
        [31] = 28,
    };

    /// <summary>A·e^{j(2π·f·n/fs + φ)}. <paramref name="amplitude"/> is peak; phase in radians.</summary>
    public static Complex[] Tone(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        var x = new Complex[numSamples];
        Tone(x, sampleRate, frequency, amplitude, phase);
        return x;
    }

    /// <summary>Fills <paramref name="destination"/> with a complex tone; see <see cref="Tone(double, int, double, double, double)"/>.</summary>
    public static void Tone(Span<Complex> destination, double sampleRate, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(sampleRate);
        double w = 2.0 * Math.PI * frequency;
        for (int n = 0; n < destination.Length; n++)
        {
            double arg = w * (n / sampleRate) + phase;
            destination[n] = new Complex(amplitude * Math.Cos(arg), amplitude * Math.Sin(arg));
        }
    }

    /// <summary>A·cos(2π·f·n/fs + φ). <paramref name="amplitude"/> is peak; phase in radians.</summary>
    public static double[] RealTone(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(sampleRate);
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        double w = 2.0 * Math.PI * frequency;
        var x = new double[numSamples];
        for (int n = 0; n < x.Length; n++)
            x[n] = amplitude * Math.Cos(w * (n / sampleRate) + phase);
        return x;
    }

    /// <summary>
    /// Maximal-length PRBS bits for the O.150 polynomial of <paramref name="order"/>. The sequence
    /// satisfies a[i] = a[i−m] XOR a[i−k] for xᵐ + xᵏ + 1. <paramref name="seed"/> gives the first m
    /// bits, first bit in the most significant position; the default is all ones.
    /// </summary>
    public static byte[] Prbs(int order, int numBits, uint? seed = null, bool invert = false)
    {
        if (!PrbsTaps.TryGetValue(order, out int k))
            throw new ArgumentOutOfRangeException(nameof(order), order,
                $"unsupported PRBS order; supported: {string.Join(", ", PrbsTaps.Keys.Order())}");
        ArgumentOutOfRangeException.ThrowIfNegative(numBits);
        int m = order;
        uint full = (uint)((1UL << m) - 1);
        uint state = seed ?? full;
        if (state == 0 || state > full)
            throw new ArgumentOutOfRangeException(nameof(seed), seed, $"must be in 1..{full}");

        var output = new byte[numBits];
        int count = (int)Math.Min(numBits, (long)full);
        // state holds the last m bits, oldest (a[i-m]) in the most significant position.
        for (int i = 0; i < count; i++)
        {
            uint bit = (state >> (m - 1)) & 1;
            output[i] = (byte)bit;
            uint next = bit ^ ((state >> (k - 1)) & 1);
            state = ((state << 1) & full) | next;
        }
        for (int i = count; i < numBits; i++)
            output[i] = output[i - count];
        if (invert)
            for (int i = 0; i < output.Length; i++)
                output[i] ^= 1;
        return output;
    }
}
