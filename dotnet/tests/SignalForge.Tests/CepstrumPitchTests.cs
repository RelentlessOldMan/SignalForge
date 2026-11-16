using Xunit;

namespace SignalForge.Tests;

/// <summary>Cepstrum pitch (conventions: Cepstrum pitch; ADR 0152).</summary>
public class CepstrumPitchTests
{
    private const double Fs = 8000;
    private const int Period = 40;

    // 401 samples: not a whole number of periods, so no bin of the spectrum is 0.
    private static double[] PulseTrain() =>
        [.. Enumerable.Range(0, 401).Select(n => (n % Period) switch { 0 => 1.0, 1 => 0.6, 2 => 0.2, _ => 0.0 })];

    [Fact]
    public void PulseTrainIsFoundAtItsPeriod()
    {
        var p = Measurements.CepstrumPitch(PulseTrain(), Fs, 80, 400);
        Assert.Equal(Period, (int)Math.Round(p.Quefrency));
        Assert.Equal(Fs / Period, p.Frequency, 2e-2 * Fs / Period);
        Assert.True(p.Strength > 0);
    }

    [Fact]
    public void ScalingLeavesItUnchanged()
    {
        var a = Measurements.CepstrumPitch(PulseTrain(), Fs, 80, 400);
        var b = Measurements.CepstrumPitch([.. PulseTrain().Select(v => -5 * v)], Fs, 80, 400);
        Assert.Equal(a.Quefrency, b.Quefrency, 1e-12);
        Assert.Equal(a.Strength, b.Strength, 1e-12);
    }
}
