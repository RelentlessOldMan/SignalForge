using Xunit;

namespace SignalForge.Tests;

/// <summary>Moving average (ADR 0241).</summary>
public class MovingAverageTests
{
    [Fact]
    public void RampSettlesToCentredValue()
    {
        double[] x = [.. Enumerable.Range(0, 20).Select(n => (double)n)];
        double[] y = Dsp.MovingAverage(x, 5);
        for (int n = 4; n < 20; n++)
            Assert.Equal(n - 2.0, y[n], 1e-14);
    }
}
