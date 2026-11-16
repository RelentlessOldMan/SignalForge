using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The mean <c>|x|²</c> over consecutive blocks of <c>⌊duration·fs + 1/2⌋</c>
    /// samples, a partial last block dropped (conventions: Short Leq series and sound exposure;
    /// ADR 0170).</summary>
    /// <param name="samples">Complex samples, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="duration">Block duration in seconds, finite and positive.</param>
    /// <returns>One mean power per whole block.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BlockLeq(ReadOnlySpan<Complex> samples, double sampleRate, double duration) =>
        Blocks(LevelPowers(samples, sampleRate), sampleRate, duration);

    /// <summary>The mean <c>x²</c> over consecutive blocks of <c>⌊duration·fs + 1/2⌋</c>
    /// samples, a partial last block dropped (conventions: Short Leq series and sound exposure;
    /// ADR 0170).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="duration">Block duration in seconds, finite and positive.</param>
    /// <returns>One mean power per whole block.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BlockLeq(ReadOnlySpan<double> samples, double sampleRate, double duration) =>
        Blocks(LevelPowers(samples, sampleRate), sampleRate, duration);

    /// <summary>The sound exposure <c>Σ|x|²/fs</c> (conventions: Short Leq series and sound
    /// exposure; ADR 0170).</summary>
    /// <param name="samples">Complex samples, finite; may be empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The exposure, in the units of <c>|x|²</c> times seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SoundExposure(ReadOnlySpan<Complex> samples, double sampleRate) =>
        Exposure(LevelPowers(samples, sampleRate), sampleRate);

    /// <summary>The sound exposure <c>Σx²/fs</c> (conventions: Short Leq series and sound
    /// exposure; ADR 0170).</summary>
    /// <param name="samples">Real samples, finite; may be empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The exposure, in the units of <c>x²</c> times seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SoundExposure(ReadOnlySpan<double> samples, double sampleRate) =>
        Exposure(LevelPowers(samples, sampleRate), sampleRate);

    private static double[] LevelPowers(ReadOnlySpan<Complex> samples, double sampleRate)
    {
        var p = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            if (!(double.IsFinite(samples[n].Real) && double.IsFinite(samples[n].Imaginary)))
                throw new ArgumentException("samples must be finite", nameof(samples));
            p[n] = samples[n].Real * samples[n].Real + samples[n].Imaginary * samples[n].Imaginary;
        }
        return CheckLevelRate(p, sampleRate);
    }

    private static double[] LevelPowers(ReadOnlySpan<double> samples, double sampleRate)
    {
        var p = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            p[n] = samples[n] * samples[n];
        }
        return CheckLevelRate(p, sampleRate);
    }

    private static double[] CheckLevelRate(double[] p, double sampleRate) =>
        double.IsFinite(sampleRate) && sampleRate > 0 ? p
            : throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");

    private static double[] Blocks(double[] p, double sampleRate, double duration)
    {
        if (!(double.IsFinite(duration) && duration > 0))
            throw new ArgumentOutOfRangeException(nameof(duration), duration, "must be finite and positive");
        double size = Math.Floor(duration * sampleRate + 0.5);
        if (size < 1)
            throw new ArgumentOutOfRangeException(nameof(duration), duration, "duration * sampleRate must round to at least 1 sample");
        long n = size >= p.Length + 1.0 ? p.Length + 1L : (long)size;
        var output = new double[p.Length / n];
        for (int i = 0; i < output.Length; i++)
        {
            double sum = 0;
            for (long k = i * n; k < (i + 1) * n; k++)
                sum += p[k];
            output[i] = sum / n;
        }
        return output;
    }

    private static double Exposure(double[] p, double sampleRate)
    {
        double sum = 0;
        foreach (double v in p)
            sum += v;
        return sum / sampleRate;
    }
}
