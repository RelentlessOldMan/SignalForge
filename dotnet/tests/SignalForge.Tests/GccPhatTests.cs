using Xunit;

namespace SignalForge.Tests;

/// <summary>GCC-PHAT delay (conventions: GCC-PHAT delay; ADR 0191).</summary>
public class GccPhatTests
{
    [Fact]
    public void ADelayedNoiseBurstIsFound()
    {
        var rng = new Random(37);
        var s = new double[1200];
        for (int n = 0; n < s.Length; n++)
            s[n] = rng.NextDouble() - 0.5;
        var r = Measurements.GccPhat(s.AsSpan(100, 1000), s.AsSpan(137, 1000), 8000);
        Assert.Equal(37, r.Lag);
        Assert.True(Math.Abs(r.Delay - 37.0 / 8000) < 0.5 / 8000);
    }
}
