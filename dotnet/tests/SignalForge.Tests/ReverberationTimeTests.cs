using Xunit;

namespace SignalForge.Tests;

/// <summary>Reverberation time (conventions: Reverberation time; ADR 0171).</summary>
public class ReverberationTimeTests
{
    [Fact]
    public void ExponentiallyDecayingNoiseGivesItsDesignTime()
    {
        const double fs = 8000, t60 = 0.5;
        var rng = new Random(8);
        var ir = new double[16000];
        for (int n = 0; n < ir.Length; n++)
            ir[n] = Math.Pow(10, -3.0 * n / (t60 * fs)) * (rng.NextDouble() - 0.5);
        Assert.Equal(t60, Measurements.ReverberationTime(ir, fs), 0.025);
        Assert.Equal(t60, Measurements.ReverberationTime(ir, fs, stopDb: -35), 0.025);
    }
}
