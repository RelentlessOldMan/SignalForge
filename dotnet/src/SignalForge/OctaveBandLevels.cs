using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The mean power in each band of <see cref="Units.OctaveBands"/>, through a
    /// Butterworth band-pass from rest (conventions: Octave-band levels; ADR 0168).</summary>
    /// <param name="samples">Complex samples, finite, not empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="fraction">Bands per octave, at least 1.</param>
    /// <param name="minFrequency">The lowest mid-band frequency in Hz.</param>
    /// <param name="maxFrequency">The highest mid-band frequency in Hz.</param>
    /// <param name="order">The Butterworth prototype order, at least 1.</param>
    /// <returns>One mean power per band, in band order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] OctaveBandLevels(ReadOnlySpan<Complex> samples, double sampleRate, int fraction,
        double minFrequency, double maxFrequency, int order = 3)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
            if (!(double.IsFinite(v.Real) && double.IsFinite(v.Imaginary)))
                throw new ArgumentException("samples must be finite", nameof(samples));
        double[][] bands = LevelBands(sampleRate, fraction, minFrequency, maxFrequency, order);
        var output = new double[bands.Length];
        for (int i = 0; i < bands.Length; i++)
        {
            Complex[] y = new IirFilter(Dsp.ButterworthBandpass(order, bands[i][0], bands[i][2], sampleRate)).Process(samples);
            double sum = 0;
            foreach (Complex v in y)
                sum += v.Real * v.Real + v.Imaginary * v.Imaginary;
            output[i] = sum / y.Length;
        }
        return output;
    }

    /// <summary>The mean power in each band of <see cref="Units.OctaveBands"/>, through a
    /// Butterworth band-pass from rest (conventions: Octave-band levels; ADR 0168).</summary>
    /// <param name="samples">Real samples, finite, not empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="fraction">Bands per octave, at least 1.</param>
    /// <param name="minFrequency">The lowest mid-band frequency in Hz.</param>
    /// <param name="maxFrequency">The highest mid-band frequency in Hz.</param>
    /// <param name="order">The Butterworth prototype order, at least 1.</param>
    /// <returns>One mean power per band, in band order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] OctaveBandLevels(ReadOnlySpan<double> samples, double sampleRate, int fraction,
        double minFrequency, double maxFrequency, int order = 3)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        double[][] bands = LevelBands(sampleRate, fraction, minFrequency, maxFrequency, order);
        var output = new double[bands.Length];
        for (int i = 0; i < bands.Length; i++)
        {
            double[] y = new IirFilter(Dsp.ButterworthBandpass(order, bands[i][0], bands[i][2], sampleRate)).Process(samples);
            double sum = 0;
            foreach (double v in y)
                sum += v * v;
            output[i] = sum / y.Length;
        }
        return output;
    }

    private static double[][] LevelBands(double sampleRate, int fraction, double minFrequency, double maxFrequency, int order)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (order < 1)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be at least 1");
        double[][] bands = Units.OctaveBands(fraction, minFrequency, maxFrequency);
        if (bands.Length > 0 && bands[^1][2] >= sampleRate / 2)
            throw new ArgumentException("every band's upper edge must be below sampleRate / 2", nameof(maxFrequency));
        return bands;
    }
}
