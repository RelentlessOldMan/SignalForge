using Xunit;

namespace SignalForge.Tests;

/// <summary>Autocorrelation pitch (conventions: Autocorrelation pitch; ADR 0150).</summary>
public class AutocorrelationPitchTests
{
    private const double Fs = 8000, F0 = 8000 / 36.6;

    private static double[] Signal() =>
        [.. Enumerable.Range(0, 1200).Select(n => Math.Sin(2 * Math.PI * F0 * n / Fs) + 0.4 * Math.Sin(4 * Math.PI * F0 * n / Fs))];

    [Fact]
    public void RecoversANonIntegerPeriod()
    {
        var p = Measurements.AutocorrelationPitch(Signal(), Fs, 80, 500);
        Assert.Equal(F0, p.Frequency, 5e-3 * F0);
        Assert.True(p.Voicing > 0.9);
    }

    [Fact]
    public void ScalingLeavesItUnchanged()
    {
        double[] x = Signal();
        var a = Measurements.AutocorrelationPitch(x, Fs, 80, 500);
        var b = Measurements.AutocorrelationPitch([.. x.Select(v => -3 * v)], Fs, 80, 500);
        Assert.Equal(a.Frequency, b.Frequency, 1e-9 * a.Frequency);
        Assert.Equal(a.Voicing, b.Voicing, 1e-12);
    }
}
