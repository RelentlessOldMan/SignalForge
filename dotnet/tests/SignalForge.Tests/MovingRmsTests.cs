using Xunit;

namespace SignalForge.Tests;

/// <summary>Moving RMS (ADR 0239).</summary>
public class MovingRmsTests
{
    [Fact]
    public void SineRms()
    {
        double[] x = [.. Enumerable.Range(0, 1000).Select(n => 2 * Math.Sin(2 * Math.PI * n / 20))];
        double[] y = Dsp.MovingRms(x, 100);
        for (int n = 99; n < 1000; n++)
            Assert.True(Math.Abs(y[n] - Math.Sqrt(2)) < 1e-12, $"sample {n}");
    }
}
