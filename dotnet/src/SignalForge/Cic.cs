using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>The <paramref name="stages"/>-fold convolution of <c>factor·delay</c> ones: the CIC
    /// response, unnormalized, with DC gain <c>(factor·delay)^stages</c> (conventions: CIC
    /// decimator; ADR 0229).</summary>
    /// <param name="factor">The decimation factor <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of stages <c>N</c>, 1 to 64.</param>
    /// <param name="delay">The comb delay <c>M</c> at the low rate, at least 1.</param>
    /// <returns><c>N(RM − 1) + 1</c> taps, each an exact integer.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the gain exceeds 2^53.</exception>
    public static double[] CicTaps(int factor, int stages, int delay = 1)
    {
        if (factor < 1 || stages < 1 || delay < 1)
            throw new ArgumentOutOfRangeException(nameof(factor), "factor, stages and delay must be at least 1");
        if (stages > 64)
            throw new ArgumentOutOfRangeException(nameof(stages), "stages must be at most 64");
        double rm = (double)factor * delay, gain = 1;
        for (int s = 0; s < stages; s++)
        {
            gain *= rm;
            if (gain > 9007199254740992.0)
                throw new ArgumentException("(factor * delay)^stages must be at most 2^53", nameof(stages));
        }
        int box = (int)rm;
        double[] h = [1.0];
        for (int s = 0; s < stages; s++)
        {
            var next = new double[h.Length + box - 1];
            for (int i = 0; i < h.Length; i++)
            {
                for (int j = 0; j < box; j++)
                    next[i + j] += h[i];
            }
            h = next;
        }
        return h;
    }

    /// <summary>CIC decimation of real samples: <c>y[k] = Σ_m h[m]·x[k·factor − m]</c> with
    /// <c>h</c> from <see cref="CicTaps"/>, causal, unnormalized (conventions: CIC decimator;
    /// ADR 0229).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="factor">The decimation factor <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of stages <c>N</c>, 1 to 64.</param>
    /// <param name="delay">The comb delay <c>M</c>, at least 1.</param>
    /// <returns><c>⌈L/R⌉</c> outputs, the first at input sample 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CicDecimate(ReadOnlySpan<double> samples, int factor, int stages, int delay = 1) =>
        [.. CicDecimate((ReadOnlySpan<Complex>)ToComplexArray(samples), factor, stages, delay).Select(v => v.Real)];

    /// <summary>CIC decimation of complex samples: <c>y[k] = Σ_m h[m]·x[k·factor − m]</c> with
    /// <c>h</c> from <see cref="CicTaps"/>, causal, unnormalized (conventions: CIC decimator;
    /// ADR 0229).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="factor">The decimation factor <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of stages <c>N</c>, 1 to 64.</param>
    /// <param name="delay">The comb delay <c>M</c>, at least 1.</param>
    /// <returns><c>⌈L/R⌉</c> outputs, the first at input sample 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] CicDecimate(ReadOnlySpan<Complex> samples, int factor, int stages, int delay = 1)
    {
        double[] h = CicTaps(factor, stages, delay);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length, count = (n + factor - 1) / factor;
        var y = new Complex[count];
        for (int k = 0; k < count; k++)
        {
            int at = k * factor;
            Complex acc = Complex.Zero;
            for (int m = 0; m < h.Length && m <= at; m++)
                acc += h[m] * samples[at - m];
            y[k] = acc;
        }
        return y;
    }

    /// <summary>CIC interpolation of real samples by <paramref name="factor"/>: the zero-stuffed
    /// input through <see cref="CicTaps"/>, causal, unnormalized (conventions: CIC interpolator;
    /// ADR 0230).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="factor">The interpolation factor <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of stages <c>N</c>, 1 to 64.</param>
    /// <param name="delay">The comb delay <c>M</c> at the low rate, at least 1.</param>
    /// <returns><c>L·R</c> outputs at the high rate.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CicInterpolate(ReadOnlySpan<double> samples, int factor, int stages, int delay = 1) =>
        [.. CicInterpolate((ReadOnlySpan<Complex>)ToComplexArray(samples), factor, stages, delay).Select(v => v.Real)];

    /// <summary>CIC interpolation of complex samples by <paramref name="factor"/>: the zero-stuffed
    /// input through <see cref="CicTaps"/>, causal, unnormalized (conventions: CIC interpolator;
    /// ADR 0230).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="factor">The interpolation factor <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of stages <c>N</c>, 1 to 64.</param>
    /// <param name="delay">The comb delay <c>M</c> at the low rate, at least 1.</param>
    /// <returns><c>L·R</c> outputs at the high rate.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] CicInterpolate(ReadOnlySpan<Complex> samples, int factor, int stages, int delay = 1)
    {
        double[] h = CicTaps(factor, stages, delay);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new Complex[samples.Length * factor];
        for (int n = 0; n < y.Length; n++)
        {
            Complex acc = Complex.Zero;
            for (int m = n % factor; m < h.Length && m <= n; m += factor)
                acc += h[m] * samples[(n - m) / factor];
            y[n] = acc;
        }
        return y;
    }

    /// <summary>Type-1 frequency-sampling FIR at the low rate whose gain is the inverse of the
    /// CIC droop up to <paramref name="cutoff"/> (conventions: CIC droop compensator; ADR
    /// 0232).</summary>
    /// <param name="factor">The CIC rate change <c>R</c>, at least 1.</param>
    /// <param name="stages">The number of CIC stages <c>N</c>, 1 to 64.</param>
    /// <param name="numTaps">The number of taps, odd and at least 1.</param>
    /// <param name="cutoff">The passband edge in Hz, in <c>(0, sampleRate/(2M)]</c>.</param>
    /// <param name="sampleRate">The low rate in Hz.</param>
    /// <param name="delay">The CIC comb delay <c>M</c>, at least 1.</param>
    /// <returns>The taps.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CicCompensator(int factor, int stages, int numTaps, double cutoff, double sampleRate, int delay = 1)
    {
        if (factor < 1)
            throw new ArgumentOutOfRangeException(nameof(factor), "factor must be at least 1");
        if (stages < 1 || stages > 64)
            throw new ArgumentOutOfRangeException(nameof(stages), "stages must be in 1 ... 64");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 1");
        if (numTaps < 1 || numTaps % 2 == 0)
            throw new ArgumentOutOfRangeException(nameof(numTaps), "numTaps must be odd and at least 1");
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (!double.IsFinite(cutoff) || !(cutoff > 0) || !(cutoff <= fs / (2.0 * delay)))
            throw new ArgumentOutOfRangeException(nameof(cutoff), "cutoff must be in (0, sampleRate / (2 * delay)]");
        int c = (numTaps - 1) / 2;
        double edge = cutoff / fs;
        var d = new double[c + 1];
        for (int j = 0; j <= c; j++)
        {
            double f = (double)j / numTaps;
            if (f > edge)
                continue;
            if (j == 0)
            {
                d[j] = 1.0;
                continue;
            }
            double a = Math.Pow(Math.Abs(Math.Sin(Math.PI * delay * f) / ((double)factor * delay * Math.Sin(Math.PI * f / factor))), stages);
            double g = a > 0 ? 1.0 / a : double.PositiveInfinity;
            if (!double.IsFinite(g))
                throw new ArgumentException("the compensation gain overflows", nameof(stages));
            d[j] = g;
        }
        var h = new double[numTaps];
        for (int i = 0; i < numTaps; i++)
        {
            double acc = d[0];
            for (int j = 1; j <= c; j++)
                acc += 2.0 * d[j] * Math.Cos(2.0 * Math.PI * j * (i - c) / numTaps);
            h[i] = acc / numTaps;
        }
        return h;
    }
}
