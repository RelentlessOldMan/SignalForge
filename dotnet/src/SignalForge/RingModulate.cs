using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Multiplies real samples by the carrier <c>cos(2π·f·n/fs + phase)</c>
    /// (conventions: Ring modulator; ADR 0260).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="frequency">The carrier frequency in Hz, finite.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <param name="phase">The carrier phase in radians, finite.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] RingModulate(ReadOnlySpan<double> samples, double frequency, double sampleRate, double phase = 0)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] c = RingCarrier(samples.Length, frequency, sampleRate, phase);
        for (int n = 0; n < c.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            c[n] = samples[n] * c[n];
        }
        return c;
    }

    /// <summary>Multiplies complex samples by the carrier <c>cos(2π·f·n/fs + phase)</c>
    /// (conventions: Ring modulator; ADR 0260).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="frequency">The carrier frequency in Hz, finite.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <param name="phase">The carrier phase in radians, finite.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] RingModulate(ReadOnlySpan<Complex> samples, double frequency, double sampleRate, double phase = 0)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] c = RingCarrier(samples.Length, frequency, sampleRate, phase);
        var y = new Complex[c.Length];
        for (int n = 0; n < c.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = new Complex(v.Real * c[n], v.Imaginary * c[n]);
        }
        return y;
    }

    private static double[] RingCarrier(int length, double frequency, double sampleRate, double phase)
    {
        if (!double.IsFinite(frequency))
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must be finite");
        if (!double.IsFinite(sampleRate) || !(sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sample_rate must be positive");
        if (!double.IsFinite(phase))
            throw new ArgumentOutOfRangeException(nameof(phase), "phase must be finite");
        double w = 2.0 * Math.PI * frequency;
        var c = new double[length];
        for (int n = 0; n < length; n++)
            c[n] = Math.Cos(w * (n / sampleRate) + phase);
        return c;
    }

    /// <summary>Multiplies real samples by the tremolo gain
    /// <c>1 − depth·(1 − cos(2π·rate·n/fs))/2</c> (conventions: Tremolo; ADR 0261).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="rate">The oscillator rate in Hz, finite.</param>
    /// <param name="depth">The depth, in [0, 1]; the gain falls to <c>1 − depth</c>.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Tremolo(ReadOnlySpan<double> samples, double rate, double depth, double sampleRate)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] g = TremoloGain(samples.Length, rate, depth, sampleRate);
        for (int n = 0; n < g.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            g[n] = samples[n] * g[n];
        }
        return g;
    }

    /// <summary>Multiplies complex samples by the tremolo gain
    /// <c>1 − depth·(1 − cos(2π·rate·n/fs))/2</c> (conventions: Tremolo; ADR 0261).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="rate">The oscillator rate in Hz, finite.</param>
    /// <param name="depth">The depth, in [0, 1]; the gain falls to <c>1 − depth</c>.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Tremolo(ReadOnlySpan<Complex> samples, double rate, double depth, double sampleRate)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] g = TremoloGain(samples.Length, rate, depth, sampleRate);
        var y = new Complex[g.Length];
        for (int n = 0; n < g.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = new Complex(v.Real * g[n], v.Imaginary * g[n]);
        }
        return y;
    }

    private static double[] TremoloGain(int length, double rate, double depth, double sampleRate)
    {
        if (!double.IsFinite(depth) || !(depth >= 0 && depth <= 1))
            throw new ArgumentOutOfRangeException(nameof(depth), "depth must be in [0, 1]");
        double[] c = RingCarrier(length, rate, sampleRate, 0);
        for (int n = 0; n < length; n++)
            c[n] = 1 - depth * (1 - c[n]) / 2;
        return c;
    }

    /// <summary>Reads real samples through a delay <c>delay + depth·cos((2π·rate)·(n/fs))</c>
    /// samples, linearly interpolated, from rest (conventions: Vibrato; ADR 0271).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Vibrato(ReadOnlySpan<double> samples, double delay, double depth, double rate, double sampleRate)
    {
        CheckVibrato(delay, depth);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        return VibratoRead(samples, delay, depth, RingCarrier(samples.Length, rate, sampleRate, 0));
    }

    private static double[] VibratoRead(ReadOnlySpan<double> samples, double delay, double depth, double[] c)
    {
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double p = n - (delay + depth * c[n]);
            double fl = Math.Floor(p);
            double f = p - fl;
            long i = (long)fl;
            double lo = i >= 0 ? samples[(int)i] : 0, hi = i + 1 >= 0 && f > 0 ? samples[(int)(i + 1)] : 0;
            y[n] = lo * (1 - f) + hi * f;
        }
        return y;
    }

    /// <summary>Reads complex samples through a delay <c>delay + depth·cos((2π·rate)·(n/fs))</c>
    /// samples, linearly interpolated part by part, from rest (conventions: Vibrato;
    /// ADR 0271).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Vibrato(ReadOnlySpan<Complex> samples, double delay, double depth, double rate, double sampleRate)
    {
        CheckVibrato(delay, depth);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        return VibratoRead(samples, delay, depth, RingCarrier(samples.Length, rate, sampleRate, 0));
    }

    private static Complex[] VibratoRead(ReadOnlySpan<Complex> samples, double delay, double depth, double[] c)
    {
        var y = new Complex[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double p = n - (delay + depth * c[n]);
            double fl = Math.Floor(p);
            double f = p - fl, u = 1 - f;
            long i = (long)fl;
            Complex lo = i >= 0 ? samples[(int)i] : Complex.Zero, hi = i + 1 >= 0 && f > 0 ? samples[(int)(i + 1)] : Complex.Zero;
            y[n] = new Complex(lo.Real * u + hi.Real * f, lo.Imaginary * u + hi.Imaginary * f);
        }
        return y;
    }

    private static void CheckVibrato(double delay, double depth)
    {
        if (!double.IsFinite(delay) || delay < 0)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 0");
        if (!double.IsFinite(depth) || depth < 0 || depth > delay)
            throw new ArgumentOutOfRangeException(nameof(depth), "depth must be from 0 to delay");
    }

    /// <summary>The vibrato on real samples mixed with the dry signal,
    /// <c>x·(1 − mix) + v·mix</c> (conventions: Flanger; ADR 0272).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Flanger(ReadOnlySpan<double> samples, double delay, double depth, double rate, double sampleRate, double mix)
    {
        CheckMix(mix);
        double[] v = Vibrato(samples, delay, depth, rate, sampleRate);
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
            y[n] = samples[n] * (1 - mix) + v[n] * mix;
        return y;
    }

    /// <summary>The vibrato on complex samples mixed with the dry signal part by part,
    /// <c>x·(1 − mix) + v·mix</c> (conventions: Flanger; ADR 0272).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Flanger(ReadOnlySpan<Complex> samples, double delay, double depth, double rate, double sampleRate, double mix)
    {
        CheckMix(mix);
        Complex[] v = Vibrato(samples, delay, depth, rate, sampleRate);
        double u = 1 - mix;
        var y = new Complex[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            Complex x = samples[n];
            y[n] = new Complex(x.Real * u + v[n].Real * mix, x.Imaginary * u + v[n].Imaginary * mix);
        }
        return y;
    }

    private static void CheckMix(double mix)
    {
        if (!double.IsFinite(mix) || mix < 0 || mix > 1)
            throw new ArgumentOutOfRangeException(nameof(mix), "mix must be in [0, 1]");
    }

    /// <summary>The mean of <paramref name="voices"/> vibratos on real samples with LFO phases
    /// <c>2πk/voices</c>, mixed with the dry signal (conventions: Chorus; ADR 0273).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="voices">The number of delayed copies, at least 1.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Chorus(ReadOnlySpan<double> samples, double delay, double depth, double rate, double sampleRate, int voices, double mix)
    {
        CheckChorus(voices, mix);
        double[] wet = Vibrato(samples, delay, depth, rate, sampleRate);
        for (int k = 1; k < voices; k++)
        {
            double[] v = VibratoRead(samples, delay, depth, RingCarrier(samples.Length, rate, sampleRate, 2.0 * Math.PI * k / voices));
            for (int n = 0; n < wet.Length; n++)
                wet[n] += v[n];
        }
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
            y[n] = samples[n] * (1 - mix) + wet[n] / voices * mix;
        return y;
    }

    /// <summary>The mean of <paramref name="voices"/> vibratos on complex samples with LFO
    /// phases <c>2πk/voices</c>, mixed with the dry signal part by part (conventions: Chorus;
    /// ADR 0273).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The centre delay, samples, finite and at least 0.</param>
    /// <param name="depth">The delay swing, samples, from 0 to <paramref name="delay"/>.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="voices">The number of delayed copies, at least 1.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Chorus(ReadOnlySpan<Complex> samples, double delay, double depth, double rate, double sampleRate, int voices, double mix)
    {
        CheckChorus(voices, mix);
        Complex[] wet = Vibrato(samples, delay, depth, rate, sampleRate);
        for (int k = 1; k < voices; k++)
        {
            Complex[] v = VibratoRead(samples, delay, depth, RingCarrier(samples.Length, rate, sampleRate, 2.0 * Math.PI * k / voices));
            for (int n = 0; n < wet.Length; n++)
                wet[n] = new Complex(wet[n].Real + v[n].Real, wet[n].Imaginary + v[n].Imaginary);
        }
        double u = 1 - mix;
        var y = new Complex[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            Complex x = samples[n];
            double wr = wet[n].Real / voices, wi = wet[n].Imaginary / voices;
            y[n] = new Complex(x.Real * u + wr * mix, x.Imaginary * u + wi * mix);
        }
        return y;
    }

    private static void CheckChorus(int voices, double mix)
    {
        if (voices < 1)
            throw new ArgumentOutOfRangeException(nameof(voices), "voices must be at least 1");
        CheckMix(mix);
    }
}
