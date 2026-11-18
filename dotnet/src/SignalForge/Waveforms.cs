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

    /// <summary>Attack-decay-sustain-release envelope in whole samples, let go at
    /// <paramref name="gate"/> (conventions: ADSR envelope; ADR 0303).</summary>
    /// <param name="numSamples">The length, at least 1.</param>
    /// <param name="attack">The rise from 0 to 1, in samples, at least 0.</param>
    /// <param name="decay">The fall from 1 to the sustain level, in samples, at least 0.</param>
    /// <param name="sustain">The held level, in [0, 1].</param>
    /// <param name="release">The fall to 0 after the gate, in samples, at least 0.</param>
    /// <param name="gate">The sample where the key is let go, at least 0.</param>
    /// <returns>The envelope, <paramref name="numSamples"/> values.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Adsr(int numSamples, int attack, int decay, double sustain, int release, int gate)
    {
        if (numSamples < 1)
            throw new ArgumentOutOfRangeException(nameof(numSamples), "numSamples must be at least 1");
        if (attack < 0)
            throw new ArgumentOutOfRangeException(nameof(attack), "attack must be at least 0");
        if (decay < 0)
            throw new ArgumentOutOfRangeException(nameof(decay), "decay must be at least 0");
        if (release < 0)
            throw new ArgumentOutOfRangeException(nameof(release), "release must be at least 0");
        if (gate < 0)
            throw new ArgumentOutOfRangeException(nameof(gate), "gate must be at least 0");
        if (!(sustain >= 0 && sustain <= 1))
            throw new ArgumentOutOfRangeException(nameof(sustain), "sustain must be in [0, 1]");

        double Held(long n)
        {
            if (n < attack)
                return (double)n / attack;
            if (n < (long)attack + decay)
                return 1 - ((1 - sustain) * ((double)(n - attack) / decay));
            return sustain;
        }

        double level = Held(gate);
        var output = new double[numSamples];
        for (int n = 0; n < numSamples; n++)
        {
            long k = (long)n - gate;
            if (k < 0)
                output[n] = Held(n);
            else if (k < release)
                output[n] = level * (1 - ((double)k / release));
        }
        return output;
    }

    /// <summary>Naive sawtooth <c>A·(2u − 1)</c>, with <c>u</c> the phase in cycles
    /// (conventions: Oscillators; ADR 0305).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Sawtooth(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        for (int n = 0; n < u.Length; n++)
            u[n] = amplitude * ((2 * u[n]) - 1);
        return u;
    }

    /// <summary>Naive square: <paramref name="amplitude"/> for the first
    /// <paramref name="duty"/> of each cycle and its negative after (conventions: Oscillators;
    /// ADR 0305).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite.</param>
    /// <param name="duty">The high fraction of each cycle, in [0, 1].</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Square(double sampleRate, int numSamples, double frequency,
        double duty = 0.5, double amplitude = 1.0, double phase = 0.0)
    {
        if (!(duty >= 0 && duty <= 1))
            throw new ArgumentOutOfRangeException(nameof(duty), "duty must be in [0, 1]");
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        for (int n = 0; n < u.Length; n++)
            u[n] = u[n] < duty ? amplitude : -amplitude;
        return u;
    }

    /// <summary>Naive triangle <c>A·(4·|u − 1/2| − 1)</c>, peaking at the start of each cycle
    /// (conventions: Oscillators; ADR 0305).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Triangle(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        for (int n = 0; n < u.Length; n++)
            u[n] = amplitude * ((4 * Math.Abs(u[n] - 0.5)) - 1);
        return u;
    }

    private static double[] Cycle(double sampleRate, int numSamples, double frequency,
        double amplitude, double phase)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        CheckTone(frequency, amplitude, phase);
        var u = new double[numSamples];
        for (int n = 0; n < numSamples; n++)
        {
            double t = (frequency * (n / sampleRate)) + phase;
            u[n] = t - Math.Floor(t);
        }
        return u;
    }

    /// <summary>Two-operator FM, <c>A·cos(2π·fc·n/fs + I·sin(2π·fm·n/fs))</c> (conventions: FM
    /// tone; ADR 0306).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="carrier">The carrier frequency in Hz, finite.</param>
    /// <param name="modulator">The modulator frequency in Hz, finite.</param>
    /// <param name="index">The peak phase deviation in radians, finite.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] FmTone(double sampleRate, int numSamples, double carrier,
        double modulator, double index, double amplitude = 1.0)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        Check.Finite(carrier, nameof(carrier));
        Check.Finite(modulator, nameof(modulator));
        Check.Finite(index, nameof(index));
        Check.Finite(amplitude, nameof(amplitude));
        double wc = 2.0 * Math.PI * carrier, wm = 2.0 * Math.PI * modulator;
        var y = new double[numSamples];
        for (int n = 0; n < numSamples; n++)
        {
            double t = n / sampleRate;
            y[n] = amplitude * Math.Cos((wc * t) + (index * Math.Sin(wm * t)));
        }
        return y;
    }

    /// <summary>Sawtooth from its Fourier series up to the Nyquist frequency, with the phase in
    /// cycles (conventions: Band-limited sawtooth; ADR 0307).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite and not 0.</param>
    /// <param name="amplitude">The peak amplitude of the full series, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BandlimitedSawtooth(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        if (frequency == 0)
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must not be 0");
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        long top = TopHarmonic(sampleRate, frequency);
        double c = (-2 * amplitude) / Math.PI;
        for (int n = 0; n < u.Length; n++)
        {
            double acc = 0;
            for (long k = 1; k <= top; k++)
                acc += Math.Sin((2 * Math.PI * k) * u[n]) / k;
            u[n] = c * acc;
        }
        return u;
    }

    /// <summary>One cycle of <paramref name="table"/> played at <paramref name="frequency"/>
    /// with linear interpolation that wraps, the phase in cycles (conventions: Wavetable
    /// oscillator; ADR 0308).</summary>
    /// <param name="table">One cycle, real and finite, at least one entry.</param>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Wavetable(ReadOnlySpan<double> table, double sampleRate, int numSamples,
        double frequency, double phase = 0.0)
    {
        if (table.IsEmpty)
            throw new ArgumentException("table must hold at least one entry", nameof(table));
        foreach (double v in table)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("table must be finite", nameof(table));
        }
        double[] u = Cycle(sampleRate, numSamples, frequency, 1.0, phase);
        int size = table.Length;
        for (int n = 0; n < u.Length; n++)
        {
            double p = u[n] * size;
            double fi = Math.Floor(p);
            double r = p - fi;
            int i = (int)fi;
            if (i >= size)
                i -= size;
            u[n] = (table[i] * (1 - r)) + (table[(i + 1) % size] * r);
        }
        return u;
    }

    /// <summary>Square at duty 1/2 from its odd harmonics up to the Nyquist frequency, with the
    /// phase in cycles (conventions: Band-limited square and triangle; ADR 0309).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite and not 0.</param>
    /// <param name="amplitude">The peak amplitude of the full series, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BandlimitedSquare(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        if (frequency == 0)
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must not be 0");
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        long top = TopHarmonic(sampleRate, frequency);
        double c = (4 * amplitude) / Math.PI;
        for (int n = 0; n < u.Length; n++)
        {
            double acc = 0;
            for (long k = 1; k <= top; k += 2)
                acc += Math.Sin((2 * Math.PI * k) * u[n]) / k;
            u[n] = c * acc;
        }
        return u;
    }

    /// <summary>Triangle from its odd harmonics up to the Nyquist frequency, peaking at the
    /// start of each cycle, with the phase in cycles (conventions: Band-limited square and
    /// triangle; ADR 0309).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite and not 0.</param>
    /// <param name="amplitude">The peak amplitude of the full series, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BandlimitedTriangle(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        if (frequency == 0)
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must not be 0");
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        long top = TopHarmonic(sampleRate, frequency);
        double c = (8 * amplitude) / (Math.PI * Math.PI);
        for (int n = 0; n < u.Length; n++)
        {
            double acc = 0;
            for (long k = 1; k <= top; k += 2)
                acc += Math.Cos((2 * Math.PI * k) * u[n]) / (double)(k * k);
            u[n] = c * acc;
        }
        return u;
    }

    private static long TopHarmonic(double sampleRate, double frequency)
    {
        double half = 0.5 * sampleRate, af = Math.Abs(frequency);
        long top = (long)Math.Min(half / af, int.MaxValue);
        while ((top + 1) * af < half)
            top++;
        while (top > 0 && top * af >= half)
            top--;
        return top;
    }

    /// <summary>Naive sawtooth with the PolyBLEP residual taken off at the jump, with the phase
    /// in cycles (conventions: PolyBLEP sawtooth; ADR 0310).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite, with magnitude at most half the sample
    /// rate.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PolyblepSawtooth(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        if (!(Math.Abs(frequency) <= 0.5 * sampleRate))
            throw new ArgumentOutOfRangeException(nameof(frequency), "|frequency| must be at most sampleRate/2");
        double dt = Math.Abs(frequency) / sampleRate;
        for (int n = 0; n < u.Length; n++)
            u[n] = amplitude * (((2 * u[n]) - 1) - Blep(u[n], dt));
        return u;
    }

    /// <summary>The PolyBLEP residual at phase <paramref name="v"/> for a jump at 0 (ADR 0310).</summary>
    private static double Blep(double v, double dt)
    {
        if (v < dt)
        {
            double t = v / dt;
            return t + t - (t * t) - 1;
        }
        if (v > 1 - dt)
        {
            double t = (v - 1) / dt;
            return (t * t) + t + t + 1;
        }
        return 0;
    }

    /// <summary>Naive square with the PolyBLEP residual at both edges, with the phase in cycles
    /// (conventions: PolyBLEP square; ADR 0311).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite, with magnitude at most half the sample
    /// rate.</param>
    /// <param name="duty">The fraction of each cycle at <paramref name="amplitude"/>, in [0, 1].</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PolyblepSquare(double sampleRate, int numSamples, double frequency,
        double duty = 0.5, double amplitude = 1.0, double phase = 0.0)
    {
        if (!(duty >= 0 && duty <= 1))
            throw new ArgumentOutOfRangeException(nameof(duty), "duty must be in [0, 1]");
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        if (!(Math.Abs(frequency) <= 0.5 * sampleRate))
            throw new ArgumentOutOfRangeException(nameof(frequency), "|frequency| must be at most sampleRate/2");
        double dt = Math.Abs(frequency) / sampleRate;
        for (int n = 0; n < u.Length; n++)
            u[n] = BlepSquare(u[n], duty, amplitude, dt);
        return u;
    }

    /// <summary>One sample of the square with duty <paramref name="d"/> and the PolyBLEP
    /// residual at both edges (ADR 0311).</summary>
    private static double BlepSquare(double u, double d, double amplitude, double dt)
    {
        bool low = u < d;
        double v = u - d;
        if (low)
            v += 1;
        double naive = low ? amplitude : -amplitude;
        return naive + (amplitude * Blep(u, dt)) - (amplitude * Blep(v, dt));
    }

    /// <summary>Pulse-width modulation with the PolyBLEP residual at both edges, the phase in
    /// cycles (conventions: PolyBLEP pulse-width modulation; ADR 0313).</summary>
    /// <param name="duty">One duty per output sample, each in [0, 1]; may be empty.</param>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="frequency">The frequency, finite, with magnitude at most half the sample
    /// rate.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns>One sample per entry of <paramref name="duty"/>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PolyblepPwm(ReadOnlySpan<double> duty, double sampleRate,
        double frequency, double amplitude = 1.0, double phase = 0.0)
    {
        foreach (double d in duty)
        {
            if (!(d >= 0 && d <= 1))
                throw new ArgumentOutOfRangeException(nameof(duty), "duty must be in [0, 1]");
        }
        double[] u = Cycle(sampleRate, duty.Length, frequency, amplitude, phase);
        if (!(Math.Abs(frequency) <= 0.5 * sampleRate))
            throw new ArgumentOutOfRangeException(nameof(frequency), "|frequency| must be at most sampleRate/2");
        double dt = Math.Abs(frequency) / sampleRate;
        for (int n = 0; n < u.Length; n++)
            u[n] = BlepSquare(u[n], duty[n], amplitude, dt);
        return u;
    }

    /// <summary>Square whose duty changes every sample: <paramref name="amplitude"/> while the
    /// phase is below <c>duty[n]</c>, its negative after, the phase in cycles (conventions:
    /// Pulse-width modulation; ADR 0312).</summary>
    /// <param name="duty">One duty per output sample, each in [0, 1]; may be empty.</param>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="frequency">The frequency, finite.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns>One sample per entry of <paramref name="duty"/>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Pwm(ReadOnlySpan<double> duty, double sampleRate, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        foreach (double d in duty)
        {
            if (!(d >= 0 && d <= 1))
                throw new ArgumentOutOfRangeException(nameof(duty), "duty must be in [0, 1]");
        }
        double[] u = Cycle(sampleRate, duty.Length, frequency, amplitude, phase);
        for (int n = 0; n < u.Length; n++)
            u[n] = u[n] < duty[n] ? amplitude : -amplitude;
        return u;
    }

    /// <summary>Naive triangle with the PolyBLAMP residual at both corners, with the phase in
    /// cycles (conventions: PolyBLEP triangle; ADR 0314).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite, with magnitude at most half the sample
    /// rate.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PolyblepTriangle(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        if (!(Math.Abs(frequency) <= 0.5 * sampleRate))
            throw new ArgumentOutOfRangeException(nameof(frequency), "|frequency| must be at most sampleRate/2");
        double dt = Math.Abs(frequency) / sampleRate;
        for (int n = 0; n < u.Length; n++)
        {
            double v = u[n], c = 0;
            double d = Math.Min(v, 1 - v);
            if (d < dt)
            {
                double w = 1 - (d / dt);
                c -= w * w * w / 6;
            }
            d = Math.Abs(v - 0.5);
            if (d < dt)
            {
                double w = 1 - (d / dt);
                c += w * w * w / 6;
            }
            u[n] = amplitude * (((4 * Math.Abs(v - 0.5)) - 1) + (8 * dt * c));
        }
        return u;
    }

    /// <summary>Naive sawtooth at <paramref name="frequency"/> restarted each time a master at
    /// <paramref name="syncFrequency"/> starts a cycle (conventions: Hard-synced sawtooth;
    /// ADR 0315).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The slave frequency, finite.</param>
    /// <param name="syncFrequency">The master frequency, positive and finite.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] HardSyncSawtooth(double sampleRate, int numSamples, double frequency,
        double syncFrequency, double amplitude = 1.0)
    {
        double[] m = Cycle(sampleRate, numSamples, syncFrequency, amplitude, 0.0);
        if (!(syncFrequency > 0))
            throw new ArgumentOutOfRangeException(nameof(syncFrequency), "syncFrequency must be positive");
        if (!double.IsFinite(frequency))
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must be finite");
        double ratio = frequency / syncFrequency;
        for (int n = 0; n < m.Length; n++)
        {
            double s = ratio * m[n];
            m[n] = amplitude * ((2 * (s - Math.Floor(s))) - 1);
        }
        return m;
    }

    /// <summary>The mean of <paramref name="voices"/> PolyBLEP sawtooths spread evenly over
    /// ±<paramref name="detune"/> cents, voice <c>k</c> starting at phase <c>k/voices</c>
    /// (conventions: Supersaw; ADR 0316).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The centre frequency, finite.</param>
    /// <param name="detune">The spread each side in cents, finite and at least 0.</param>
    /// <param name="voices">The number of sawtooths, at least 1.</param>
    /// <param name="amplitude">The scale of the mean, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a voice is above
    /// half the sample rate.</exception>
    public static double[] Supersaw(double sampleRate, int numSamples, double frequency,
        double detune, int voices = 7, double amplitude = 1.0)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(voices, 1);
        if (!(detune >= 0 && double.IsFinite(detune)))
            throw new ArgumentOutOfRangeException(nameof(detune), "detune must be finite and at least 0");
        CheckTone(frequency, amplitude, 0.0);
        ArgumentOutOfRangeException.ThrowIfNegative(numSamples);
        var acc = new double[numSamples];
        for (int k = 0; k < voices; k++)
        {
            double cents = voices == 1 ? 0.0 : detune * ((2.0 * k / (voices - 1)) - 1);
            double[] saw = PolyblepSawtooth(sampleRate, numSamples,
                frequency * Math.Pow(2, cents / 1200), 1.0, (double)k / voices);
            for (int n = 0; n < numSamples; n++)
                acc[n] += saw[n];
        }
        for (int n = 0; n < numSamples; n++)
            acc[n] = amplitude * (acc[n] / voices);
        return acc;
    }

    /// <summary>Differentiated parabolic waveform: the scaled first difference of the squared
    /// naive sawtooth, with the phase in cycles (conventions: DPW sawtooth; ADR 0317).</summary>
    /// <param name="sampleRate">The sample rate, positive and finite.</param>
    /// <param name="numSamples">The length, at least 0.</param>
    /// <param name="frequency">The frequency, finite, with magnitude at most half the sample
    /// rate.</param>
    /// <param name="amplitude">The peak amplitude, finite.</param>
    /// <param name="phase">The starting phase in cycles, finite.</param>
    /// <returns><paramref name="numSamples"/> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] DpwSawtooth(double sampleRate, int numSamples, double frequency,
        double amplitude = 1.0, double phase = 0.0)
    {
        double[] u = Cycle(sampleRate, numSamples, frequency, amplitude, phase);
        if (!(Math.Abs(frequency) <= 0.5 * sampleRate))
            throw new ArgumentOutOfRangeException(nameof(frequency), "|frequency| must be at most sampleRate/2");
        if (frequency == 0)
        {
            for (int n = 0; n < u.Length; n++)
                u[n] = amplitude * ((2 * u[n]) - 1);
            return u;
        }
        double t = (frequency * (-1 / sampleRate)) + phase;
        double prev = (2 * (t - Math.Floor(t))) - 1;
        double scale = sampleRate / (4 * frequency);
        for (int n = 0; n < u.Length; n++)
        {
            double x = (2 * u[n]) - 1;
            u[n] = amplitude * (((x * x) - (prev * prev)) * scale);
            prev = x;
        }
        return u;
    }
}
