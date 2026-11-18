using System.Numerics;

namespace SignalForge;

/// <summary>Which response <see cref="Dsp.Svf(ReadOnlySpan{double}, double, double, double, SvfOutput)"/>
/// returns (conventions: State-variable filter; ADR 0279).</summary>
public enum SvfOutput
{
    /// <summary><c>1/(s² + k·s + 1)</c>.</summary>
    Lowpass,

    /// <summary><c>s/(s² + k·s + 1)</c>, peak gain <c>q</c>.</summary>
    Bandpass,

    /// <summary><c>s²/(s² + k·s + 1)</c>.</summary>
    Highpass,

    /// <summary><c>(s² + 1)/(s² + k·s + 1)</c>.</summary>
    Notch,
}

public static partial class Dsp
{
    /// <summary>Trapezoidal state-variable filter on real samples (conventions: State-variable
    /// filter; ADR 0279).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="cutoff">The cutoff, Hz, above 0 and below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="output">Which response to return.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Svf(ReadOnlySpan<double> samples, double cutoff, double q, double sampleRate, SvfOutput output = SvfOutput.Lowpass)
    {
        (double g, double k) = SvfCoefficients(samples.Length, cutoff, q, sampleRate, output);
        var v = new double[samples.Length];
        for (int n = 0; n < v.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            v[n] = samples[n];
        }
        return SvfRun(v, SvfConstant(g, v.Length), k, output);
    }

    /// <summary>Trapezoidal state-variable filter on complex samples, part by part
    /// (conventions: State-variable filter; ADR 0279).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="cutoff">The cutoff, Hz, above 0 and below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="output">Which response to return.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Svf(ReadOnlySpan<Complex> samples, double cutoff, double q, double sampleRate, SvfOutput output = SvfOutput.Lowpass)
    {
        (double g, double k) = SvfCoefficients(samples.Length, cutoff, q, sampleRate, output);
        var re = new double[samples.Length];
        var im = new double[samples.Length];
        for (int n = 0; n < re.Length; n++)
        {
            if (!double.IsFinite(samples[n].Real) || !double.IsFinite(samples[n].Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            re[n] = samples[n].Real;
            im[n] = samples[n].Imaginary;
        }
        double[] gs = SvfConstant(g, re.Length);
        double[] yr = SvfRun(re, gs, k, output), yi = SvfRun(im, gs, k, output);
        var y = new Complex[re.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = new Complex(yr[n], yi[n]);
        return y;
    }

    private static (double G, double K) SvfCoefficients(int length, double cutoff, double q, double sampleRate, SvfOutput output)
    {
        if (!double.IsFinite(sampleRate) || sampleRate <= 0)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sampleRate must be positive");
        if (!double.IsFinite(cutoff) || !(cutoff > 0 && cutoff < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(cutoff), "cutoff must be in (0, sampleRate / 2)");
        if (!double.IsFinite(q) || !(q > 0))
            throw new ArgumentOutOfRangeException(nameof(q), "q must be positive");
        if (output is not (SvfOutput.Lowpass or SvfOutput.Bandpass or SvfOutput.Highpass or SvfOutput.Notch))
            throw new ArgumentOutOfRangeException(nameof(output), "output must be Lowpass, Bandpass, Highpass or Notch");
        if (length == 0)
            throw new ArgumentException("samples must not be empty", nameof(length));
        return (Math.Tan(Math.PI * cutoff / sampleRate), 1 / q);
    }

    private static double[] SvfRun(double[] v, double[] g, double k, SvfOutput output)
    {
        double ic1 = 0, ic2 = 0;
        var y = new double[v.Length];
        for (int n = 0; n < v.Length; n++)
        {
            double a1 = 1 / (1 + g[n] * (g[n] + k));
            double a2 = g[n] * a1;
            double a3 = g[n] * a2;
            double x = v[n];
            double v3 = x - ic2;
            double v1 = a1 * ic1 + a2 * v3;
            double v2 = ic2 + a2 * ic1 + a3 * v3;
            ic1 = 2 * v1 - ic1;
            ic2 = 2 * v2 - ic2;
            y[n] = output switch
            {
                SvfOutput.Lowpass => v2,
                SvfOutput.Bandpass => v1,
                SvfOutput.Highpass => x - k * v1 - v2,
                _ => x - k * v1,
            };
        }
        return y;
    }

    private static double[] SvfConstant(double g, int length)
    {
        var a = new double[length];
        Array.Fill(a, g);
        return a;
    }

    /// <summary>The state-variable band-pass on real samples, unity peak, with its cutoff moved
    /// from <paramref name="low"/> to <paramref name="high"/> by the envelope, mixed with the dry
    /// signal (conventions: Auto-wah; ADR 0280).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="low">The cutoff at silence, Hz, positive.</param>
    /// <param name="high">The cutoff at an envelope of 1 or more, Hz, from
    /// <paramref name="low"/> to below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="attack">The envelope follower's attack coefficient, in [0, 1).</param>
    /// <param name="release">The envelope follower's release coefficient, in [0, 1).</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] AutoWah(ReadOnlySpan<double> samples, double low, double high, double q, double attack, double release, double sampleRate, double mix)
    {
        CheckAutoWah(low, high, q, sampleRate, mix);
        double[] g = AutoWahCoefficients(EnvelopeFollower(samples, attack, release), low, high, sampleRate);
        double k = 1 / q;
        double[] wet = SvfRun(samples.ToArray(), g, k, SvfOutput.Bandpass);
        var y = new double[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] * (1 - mix) + k * wet[n] * mix;
        return y;
    }

    /// <summary>The state-variable band-pass on complex samples, part by part, unity peak, with
    /// its cutoff moved from <paramref name="low"/> to <paramref name="high"/> by the envelope,
    /// mixed with the dry signal (conventions: Auto-wah; ADR 0280).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="low">The cutoff at silence, Hz, positive.</param>
    /// <param name="high">The cutoff at an envelope of 1 or more, Hz, from
    /// <paramref name="low"/> to below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="attack">The envelope follower's attack coefficient, in [0, 1).</param>
    /// <param name="release">The envelope follower's release coefficient, in [0, 1).</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] AutoWah(ReadOnlySpan<Complex> samples, double low, double high, double q, double attack, double release, double sampleRate, double mix)
    {
        CheckAutoWah(low, high, q, sampleRate, mix);
        double[] g = AutoWahCoefficients(EnvelopeFollower(samples, attack, release), low, high, sampleRate);
        double k = 1 / q;
        var re = new double[samples.Length];
        var im = new double[samples.Length];
        for (int n = 0; n < re.Length; n++)
        {
            re[n] = samples[n].Real;
            im[n] = samples[n].Imaginary;
        }
        double[] wr = SvfRun(re, g, k, SvfOutput.Bandpass), wi = SvfRun(im, g, k, SvfOutput.Bandpass);
        double u = 1 - mix;
        var y = new Complex[re.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = new Complex(re[n] * u + k * wr[n] * mix, im[n] * u + k * wi[n] * mix);
        return y;
    }

    private static void CheckAutoWah(double low, double high, double q, double sampleRate, double mix)
    {
        if (!double.IsFinite(sampleRate) || sampleRate <= 0)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sampleRate must be positive");
        if (!double.IsFinite(low) || !double.IsFinite(high) || !(low > 0 && low <= high && high < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(high), "need 0 < low <= high < sampleRate / 2");
        if (!double.IsFinite(q) || !(q > 0))
            throw new ArgumentOutOfRangeException(nameof(q), "q must be positive");
        CheckMix(mix);
    }

    private static double[] AutoWahCoefficients(double[] env, double low, double high, double sampleRate)
    {
        var g = new double[env.Length];
        for (int n = 0; n < g.Length; n++)
            g[n] = Math.Tan(Math.PI * (low + (high - low) * Math.Min(env[n], 1.0)) / sampleRate);
        return g;
    }

    /// <summary>Turns the signal down while its band around <paramref name="cutoff"/> is loud:
    /// the sidechain compressor keyed on the unity-peak state-variable band-pass (conventions:
    /// De-esser; ADR 0286).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="cutoff">The centre of the sibilant band, Hz, above 0 and below half the
    /// sample rate.</param>
    /// <param name="q">The band's quality factor, finite and positive.</param>
    /// <param name="thresholdDb">The key level above which the gain falls, dB.</param>
    /// <param name="ratio">The compression ratio, at least 1.</param>
    /// <param name="attack">The envelope follower's attack coefficient, in [0, 1).</param>
    /// <param name="release">The envelope follower's release coefficient, in [0, 1).</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] DeEsser(ReadOnlySpan<double> samples, double cutoff, double q, double thresholdDb, double ratio, double attack, double release, double sampleRate)
    {
        double[] key = Svf(samples, cutoff, q, sampleRate, SvfOutput.Bandpass);
        double k = 1 / q;
        for (int n = 0; n < key.Length; n++)
            key[n] = k * key[n];
        return Duck(samples, key, thresholdDb, ratio, attack, release);
    }
}
