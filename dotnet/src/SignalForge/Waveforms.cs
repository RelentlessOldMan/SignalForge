using System.Numerics;

namespace SignalForge;

/// <summary>Waveform generators: tones, multitones, chirps, pulse trains and PRBS. Definitions in
/// docs/conventions.md.</summary>
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
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        CheckTone(frequency, amplitude, phase);
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
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        CheckTone(frequency, amplitude, phase);
        double w = 2.0 * Math.PI * frequency;
        var x = new double[numSamples];
        for (int n = 0; n < x.Length; n++)
            x[n] = amplitude * Math.Cos(w * (n / sampleRate) + phase);
        return x;
    }

    /// <summary>The sum, in order, of one complex <see cref="Tone(double, int, double, double, double)"/>
    /// per frequency (conventions: Tones, Multitone).</summary>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="numSamples">Number of samples.</param>
    /// <param name="frequencies">Tone frequencies in Hz, at least one, finite.</param>
    /// <param name="amplitudes">Peak amplitude per tone; all 1 when null.</param>
    /// <param name="phases">Phase per tone in radians; all 0 when null.</param>
    public static Complex[] Multitone(double sampleRate, int numSamples, ReadOnlySpan<double> frequencies,
        double[]? amplitudes = null, double[]? phases = null)
    {
        var (a, p) = CheckMultitone(frequencies, amplitudes, phases);
        var x = Tone(sampleRate, numSamples, frequencies[0], a[0], p[0]);
        for (int k = 1; k < frequencies.Length; k++)
        {
            Complex[] t = Tone(sampleRate, numSamples, frequencies[k], a[k], p[k]);
            for (int n = 0; n < x.Length; n++)
                x[n] += t[n];
        }
        return x;
    }

    /// <summary>The sum, in order, of one <see cref="RealTone"/> per frequency (conventions: Tones,
    /// Multitone).</summary>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="numSamples">Number of samples.</param>
    /// <param name="frequencies">Tone frequencies in Hz, at least one, finite.</param>
    /// <param name="amplitudes">Peak amplitude per tone; all 1 when null.</param>
    /// <param name="phases">Phase per tone in radians; all 0 when null.</param>
    public static double[] RealMultitone(double sampleRate, int numSamples, ReadOnlySpan<double> frequencies,
        double[]? amplitudes = null, double[]? phases = null)
    {
        var (a, p) = CheckMultitone(frequencies, amplitudes, phases);
        var x = RealTone(sampleRate, numSamples, frequencies[0], a[0], p[0]);
        for (int k = 1; k < frequencies.Length; k++)
        {
            double[] t = RealTone(sampleRate, numSamples, frequencies[k], a[k], p[k]);
            for (int n = 0; n < x.Length; n++)
                x[n] += t[n];
        }
        return x;
    }

    /// <summary>Newman's low-crest-factor phases π·k²/count for k = 0 … count − 1 (conventions:
    /// Tones, Newman phases).</summary>
    /// <param name="count">Number of tones, at least 1.</param>
    public static double[] NewmanPhases(int count)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(count, 1);
        var p = new double[count];
        for (int k = 0; k < count; k++)
            p[k] = Math.PI * ((double)k * k) / count;
        return p;
    }

    /// <summary>Complex linear chirp A·e^{jθ[n]} from <paramref name="start"/> Hz at the first sample
    /// to <paramref name="stop"/> Hz at numSamples/fs (conventions: Tones, Linear chirp).</summary>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="numSamples">Number of samples.</param>
    /// <param name="start">Frequency at the first sample, Hz.</param>
    /// <param name="stop">Frequency one sample after the last, Hz.</param>
    /// <param name="amplitude">Peak amplitude.</param>
    /// <param name="phase">Phase at the first sample, radians.</param>
    public static Complex[] Chirp(double sampleRate, int numSamples, double start, double stop,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] theta = ChirpPhase(sampleRate, numSamples, start, stop, amplitude, phase);
        return [.. theta.Select(t => new Complex(amplitude * Math.Cos(t), amplitude * Math.Sin(t)))];
    }

    /// <summary>Real linear chirp A·cos θ[n]; see <see cref="Chirp"/>.</summary>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="numSamples">Number of samples.</param>
    /// <param name="start">Frequency at the first sample, Hz.</param>
    /// <param name="stop">Frequency one sample after the last, Hz.</param>
    /// <param name="amplitude">Peak amplitude.</param>
    /// <param name="phase">Phase at the first sample, radians.</param>
    public static double[] RealChirp(double sampleRate, int numSamples, double start, double stop,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] theta = ChirpPhase(sampleRate, numSamples, start, stop, amplitude, phase);
        return [.. theta.Select(t => amplitude * Math.Cos(t))];
    }

    /// <summary>Rectangular pulses in whole samples: <paramref name="amplitude"/> where
    /// (n − delay) mod period &lt; width, the floored modulo (conventions: Tones, Pulse train).</summary>
    /// <param name="numSamples">Number of samples.</param>
    /// <param name="period">Pulse period in samples, at least 1.</param>
    /// <param name="width">Pulse width in samples, 0 to period.</param>
    /// <param name="amplitude">Pulse level.</param>
    /// <param name="delay">Start of the first pulse in samples; any integer.</param>
    public static double[] PulseTrain(int numSamples, int period, int width, double amplitude = 1.0, int delay = 0)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        ArgumentOutOfRangeException.ThrowIfLessThan(period, 1);
        ArgumentOutOfRangeException.ThrowIfNegative(width);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(width, period);
        Check.Finite(amplitude, nameof(amplitude));
        var x = new double[numSamples];
        for (int n = 0; n < numSamples; n++)
        {
            long r = ((long)n - delay) % period;
            if (r < 0)
                r += period;
            x[n] = r < width ? amplitude : 0;
        }
        return x;
    }

    private static (double[] Amplitudes, double[] Phases) CheckMultitone(ReadOnlySpan<double> frequencies,
        double[]? amplitudes, double[]? phases)
    {
        if (frequencies.IsEmpty)
            throw new ArgumentException("frequencies needs at least one value", nameof(frequencies));
        double[] a = amplitudes ?? [.. Enumerable.Repeat(1.0, frequencies.Length)];
        double[] p = phases ?? new double[frequencies.Length];
        if (a.Length != frequencies.Length)
            throw new ArgumentException("amplitudes needs one value per frequency", nameof(amplitudes));
        if (p.Length != frequencies.Length)
            throw new ArgumentException("phases needs one value per frequency", nameof(phases));
        return (a, p);
    }

    private static double[] ChirpPhase(double sampleRate, int numSamples, double start, double stop,
        double amplitude, double phase)
    {
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        Check.Finite(start, nameof(start));
        Check.Finite(stop, nameof(stop));
        Check.Finite(amplitude, nameof(amplitude));
        Check.Finite(phase, nameof(phase));
        double rate = numSamples > 0 ? (stop - start) / (2 * (numSamples / fs)) : 0;
        var theta = new double[numSamples];
        for (int n = 0; n < numSamples; n++)
        {
            double t = n / fs;
            theta[n] = 2.0 * Math.PI * (start * t + rate * (t * t)) + phase;
        }
        return theta;
    }

    private static void CheckTone(double frequency, double amplitude, double phase)
    {
        Check.Finite(frequency, nameof(frequency));
        Check.Finite(amplitude, nameof(amplitude));
        Check.Finite(phase, nameof(phase));
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
