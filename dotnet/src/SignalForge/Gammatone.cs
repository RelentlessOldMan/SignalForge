namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Sampled gammatone impulse response <c>t^(N−1)·exp(−2π b ERB t)·cos(2π f_c t)</c>,
    /// scaled to unit gain at <c>f_c</c> (conventions: FIR filters, Gammatone; ADR 0161).</summary>
    /// <param name="centerFrequency">The center frequency in Hz, above 0 and below half the sample rate.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="length">Number of taps, at least 1.</param>
    /// <param name="order">The filter order <c>N</c>, at least 1.</param>
    /// <param name="bandwidthFactor">The factor <c>b</c> on the ERB, finite and positive.</param>
    /// <returns>The taps.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the response is zero at the center frequency.</exception>
    public static double[] Gammatone(double centerFrequency, double sampleRate, int length, int order = 4, double bandwidthFactor = 1.019)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentException("sampleRate must be finite and positive", nameof(sampleRate));
        if (!(double.IsFinite(centerFrequency) && centerFrequency > 0 && centerFrequency < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(centerFrequency), "need 0 < centerFrequency < sampleRate/2");
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (order < 1)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be at least 1");
        if (!(double.IsFinite(bandwidthFactor) && bandwidthFactor > 0))
            throw new ArgumentOutOfRangeException(nameof(bandwidthFactor), "bandwidthFactor must be finite and positive");
        double erb = Units.ErbBandwidth(centerFrequency);
        double w = 2 * Math.PI * centerFrequency / sampleRate;
        var taps = new double[length];
        double re = 0, im = 0;
        for (int n = 0; n < length; n++)
        {
            double t = n / sampleRate;
            double g = Math.Pow(t, order - 1) * Math.Exp(-2 * Math.PI * bandwidthFactor * erb * t) * Math.Cos(2 * Math.PI * centerFrequency * t);
            taps[n] = g;
            re += g * Math.Cos(w * n);
            im += g * Math.Sin(w * n);
        }
        double gain = Math.Sqrt(re * re + im * im);
        if (!(gain > 0))
            throw new ArgumentException("the response is zero at centerFrequency; use a longer length", nameof(length));
        for (int n = 0; n < length; n++)
            taps[n] /= gain;
        return taps;
    }
}
