namespace SignalForge;

/// <summary>DESA-2 instantaneous amplitude and frequency for <c>n = 2 … N−3</c> (conventions:
/// Energy separation; ADR 0189).</summary>
/// <param name="Amplitude">The amplitude <c>2ψ[x]/√ψ[y]</c>; NaN where an energy is not
/// positive.</param>
/// <param name="Frequency">The frequency in Hz, in <c>[0, fs/4]</c>; NaN where an energy is not
/// positive.</param>
public sealed record EnergySeparation(double[] Amplitude, double[] Frequency);

public static partial class Measurements
{
    /// <summary>DESA-2 energy separation into instantaneous amplitude and frequency
    /// (conventions: Energy separation; ADR 0189).</summary>
    /// <param name="samples">Real samples, finite, at least five.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <returns><c>N − 4</c> amplitudes and frequencies.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static EnergySeparation EnergySeparation(ReadOnlySpan<double> samples, double sampleRate)
    {
        SignalForge.Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (samples.Length < 5)
            throw new ArgumentException("samples must hold at least five values", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int count = samples.Length - 4;
        var amp = new double[count];
        var freq = new double[count];
        double scale = sampleRate / (2 * Math.PI);
        for (int i = 0; i < count; i++)
        {
            int n = i + 2;
            double px = samples[n] * samples[n] - samples[n - 1] * samples[n + 1];
            double y0 = samples[n] - samples[n - 2];
            double y1 = samples[n + 1] - samples[n - 1];
            double y2 = samples[n + 2] - samples[n];
            double py = y1 * y1 - y0 * y2;
            if (px > 0 && py > 0)
            {
                double c = Math.Clamp(1 - py / (2 * px), -1.0, 1.0);
                freq[i] = 0.5 * Math.Acos(c) * scale;
                amp[i] = 2 * px / Math.Sqrt(py);
            }
            else
            {
                freq[i] = double.NaN;
                amp[i] = double.NaN;
            }
        }
        return new EnergySeparation(amp, freq);
    }
}
