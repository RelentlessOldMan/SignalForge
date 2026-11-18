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
}
