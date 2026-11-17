using System.Numerics;

namespace SignalForge;

public static partial class Spectral
{
    /// <summary>DFT bin <paramref name="k"/> of the <paramref name="length"/> real samples ending
    /// at each sample, zeros before the start, by the sliding-DFT recursion (conventions: Sliding
    /// DFT; ADR 0231).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <param name="k">The bin, 0 to <c>N − 1</c>.</param>
    /// <returns>One value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] SlidingDft(ReadOnlySpan<double> samples, int length, int k) =>
        SlidingDft((ReadOnlySpan<Complex>)ToComplex(samples), length, k);

    /// <summary>DFT bin <paramref name="k"/> of the <paramref name="length"/> complex samples
    /// ending at each sample, zeros before the start, by the sliding-DFT recursion (conventions:
    /// Sliding DFT; ADR 0231).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <param name="k">The bin, 0 to <c>N − 1</c>.</param>
    /// <returns>One value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] SlidingDft(ReadOnlySpan<Complex> samples, int length, int k)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (k < 0 || k >= length)
            throw new ArgumentOutOfRangeException(nameof(k), "k must be in 0 ... length - 1");
        double theta = 2.0 * Math.PI * k / length;
        var w = new Complex(Math.Cos(theta), Math.Sin(theta));
        var output = new Complex[samples.Length];
        Complex s = Complex.Zero;
        for (int i = 0; i < samples.Length; i++)
        {
            Complex old = i >= length ? samples[i - length] : Complex.Zero;
            s = (s + samples[i] - old) * w;
            output[i] = s;
        }
        return output;
    }
}
