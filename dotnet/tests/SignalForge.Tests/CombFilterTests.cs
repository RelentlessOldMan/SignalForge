using Xunit;

namespace SignalForge.Tests;

/// <summary>Comb filter (ADR 0237).</summary>
public class CombFilterTests
{
    [Fact]
    public void FeedforwardNotchesItsFrequency()
    {
        int d = 8;
        double[] x = [.. Enumerable.Range(0, 4000).Select(n => Math.Cos(2 * Math.PI * n / (2 * d)))];
        double[] y = Dsp.CombFilter(x, d, 1.0);
        Assert.True(y.Skip(d).Max(Math.Abs) < 1e-12);
    }
}
