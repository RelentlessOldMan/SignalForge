using System.Collections.ObjectModel;

namespace SignalForge;

/// <summary>
/// A finite sampled signal, real (<c>double</c>) or complex baseband (<see cref="System.Numerics.Complex"/>).
/// The samples are copied in and exposed read-only; operations return new signals.
/// <see cref="Units"/> names one sample unit ("V" for volts, "FS" for full scale, null when unknown);
/// <see cref="Impedance"/> is in ohms. See docs/conventions.md.
/// </summary>
public sealed class Signal<T> where T : struct
{
    private readonly T[] _samples;

    /// <summary>Copies <paramref name="samples"/> into a new signal.</summary>
    /// <param name="samples">The samples; copied.</param>
    /// <param name="sampleRate">Samples per second; must be positive.</param>
    /// <param name="centerFrequency">Hz; the RF frequency that complex baseband 0 Hz represents.</param>
    /// <param name="timeOrigin">Time of sample 0, in seconds.</param>
    /// <param name="units">What one sample unit is ("V", "FS"), or null.</param>
    /// <param name="impedance">Reference impedance in ohms, or null; must be positive.</param>
    /// <param name="metadata">Free-form metadata; copied.</param>
    public Signal(ReadOnlySpan<T> samples, double sampleRate, double centerFrequency = 0.0,
        double timeOrigin = 0.0, string? units = null, double? impedance = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(sampleRate);
        if (impedance is { } r)
            ArgumentOutOfRangeException.ThrowIfNegativeOrZero(r, nameof(impedance));
        _samples = samples.ToArray();
        SampleRate = sampleRate;
        CenterFrequency = centerFrequency;
        TimeOrigin = timeOrigin;
        Units = units;
        Impedance = impedance;
        Metadata = new ReadOnlyDictionary<string, object?>(
            metadata is null ? new Dictionary<string, object?>() : new Dictionary<string, object?>(metadata));
    }

    /// <summary>The samples, read-only.</summary>
    public ReadOnlySpan<T> Samples => _samples;
    /// <summary>Number of samples.</summary>
    public int Length => _samples.Length;
    /// <summary>Samples per second.</summary>
    public double SampleRate { get; }
    /// <summary>Center frequency in Hz.</summary>
    public double CenterFrequency { get; }
    /// <summary>Time of sample 0, in seconds.</summary>
    public double TimeOrigin { get; }
    /// <summary>What one sample unit is ("V", "FS"), or null when unknown.</summary>
    public string? Units { get; }
    /// <summary>Reference impedance in ohms, or null.</summary>
    public double? Impedance { get; }
    /// <summary>Free-form metadata, read-only.</summary>
    public IReadOnlyDictionary<string, object?> Metadata { get; }

    /// <summary>Number of samples divided by the sample rate, in seconds.</summary>
    public double Duration => Length / SampleRate;

    /// <summary>Time of each sample: TimeOrigin + n / SampleRate.</summary>
    public double[] Times()
    {
        var t = new double[Length];
        for (int n = 0; n < t.Length; n++)
            t[n] = TimeOrigin + n / SampleRate;
        return t;
    }

    /// <summary>A copy with new samples and the same metadata.</summary>
    public Signal<T> WithSamples(ReadOnlySpan<T> samples) =>
        new(samples, SampleRate, CenterFrequency, TimeOrigin, Units, Impedance, Metadata);
}
