using System.Numerics;

namespace SignalForge;

public static partial class Spectral
{
    /// <summary>The unscaled DTFT <c>Σ x[n]·e^(−2πi f n/fs)</c> of real samples at each frequency, by
    /// the Goertzel recursion (conventions: Goertzel; ADR 0224).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="frequencies">Frequencies in Hz, finite, at least one; any value, not only bins.</param>
    /// <returns>One complex value per frequency; at <c>f = k·fs/N</c> it equals FFT bin <c>k</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Goertzel(ReadOnlySpan<double> samples, double sampleRate, ReadOnlySpan<double> frequencies) =>
        Goertzel((ReadOnlySpan<Complex>)ToComplex(samples), sampleRate, frequencies);

    /// <summary>The unscaled DTFT <c>Σ x[n]·e^(−2πi f n/fs)</c> of complex samples at each frequency,
    /// by the Goertzel recursion (conventions: Goertzel; ADR 0224).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="frequencies">Frequencies in Hz, finite, at least one; any value, not only bins.</param>
    /// <returns>One complex value per frequency; at <c>f = k·fs/N</c> it equals FFT bin <c>k</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Goertzel(ReadOnlySpan<Complex> samples, double sampleRate, ReadOnlySpan<double> frequencies)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (frequencies.IsEmpty)
            throw new ArgumentException("frequencies must not be empty", nameof(frequencies));
        foreach (double f in frequencies)
        {
            if (!double.IsFinite(f))
                throw new ArgumentException("frequencies must be finite", nameof(frequencies));
        }
        int n = samples.Length;
        var result = new Complex[frequencies.Length];
        for (int i = 0; i < frequencies.Length; i++)
        {
            double w = 2.0 * Math.PI * frequencies[i] / sampleRate;
            double c = 2.0 * Math.Cos(w);
            Complex s1 = Complex.Zero, s2 = Complex.Zero;
            foreach (Complex v in samples)
            {
                Complex s0 = v + c * s1 - s2;
                s2 = s1;
                s1 = s0;
            }
            var turn = new Complex(Math.Cos(w), -Math.Sin(w));
            var phase = new Complex(Math.Cos(w * (n - 1)), -Math.Sin(w * (n - 1)));
            result[i] = phase * (s1 - turn * s2);
        }
        return result;
    }
}
