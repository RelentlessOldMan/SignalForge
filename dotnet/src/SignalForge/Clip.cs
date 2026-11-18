using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Cubic soft clipper <c>x − x³/3</c> on <c>[−1, 1]</c>, held at <c>±2/3</c>
    /// beyond (conventions: Cubic soft clipper; ADR 0250).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SoftClip(ReadOnlySpan<double> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = Math.Abs(v) < 1 ? v - v * v * v / 3 : Math.Sign(v) * (2.0 / 3.0);
        }
        return y;
    }

    /// <summary>Clamps real samples to <c>[−limit, limit]</c> (conventions: Hard clipper;
    /// ADR 0251).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="limit">The clipping level, finite and at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] HardClip(ReadOnlySpan<double> samples, double limit)
    {
        CheckHardClip(limit);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = Math.Min(Math.Max(v, -limit), limit);
        }
        return y;
    }

    /// <summary>Scales complex samples whose magnitude exceeds <paramref name="limit"/> back to
    /// it, keeping the phase (conventions: Hard clipper; ADR 0251).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="limit">The clipping level, finite and at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] HardClip(ReadOnlySpan<Complex> samples, double limit)
    {
        CheckHardClip(limit);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new Complex[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            double m = Complex.Abs(v);
            y[n] = m > limit ? v * (limit / m) : v;
        }
        return y;
    }

    private static void CheckHardClip(double limit)
    {
        if (!double.IsFinite(limit) || !(limit >= 0))
            throw new ArgumentOutOfRangeException(nameof(limit), "limit must be at least 0");
    }

    /// <summary>Folds samples back into <c>[−limit, limit]</c> by reflecting about each limit,
    /// the triangle wave of period <c>4·limit</c> (conventions: Wavefolder; ADR 0252).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="limit">The folding level, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Wavefold(ReadOnlySpan<double> samples, double limit)
    {
        if (!double.IsFinite(limit) || !(limit > 0))
            throw new ArgumentOutOfRangeException(nameof(limit), "limit must be positive");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double period = 4 * limit;
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            double u = v + limit;
            double t = u - period * Math.Floor(u / period);
            y[n] = limit - Math.Abs(t - 2 * limit);
        }
        return y;
    }

    /// <summary>Full-wave <c>|x|</c> or half-wave <c>max(x, 0)</c> rectifier (conventions:
    /// Rectifier; ADR 0253).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="full">True for full wave, false for half wave.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Rectify(ReadOnlySpan<double> samples, bool full = true)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = full ? Math.Abs(v) : v > 0 ? v : 0.0;
        }
        return y;
    }

    /// <summary>Tanh saturator <c>tanh(drive·x) / tanh(drive)</c>, unity at <c>x = ±1</c>
    /// (conventions: Tanh saturator; ADR 0259).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="drive">How hard the samples are pushed, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Saturate(ReadOnlySpan<double> samples, double drive)
    {
        if (!double.IsFinite(drive) || !(drive > 0))
            throw new ArgumentOutOfRangeException(nameof(drive), "drive must be positive");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double norm = Math.Tanh(drive);
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = Math.Tanh(drive * v) / norm;
        }
        return y;
    }
}
