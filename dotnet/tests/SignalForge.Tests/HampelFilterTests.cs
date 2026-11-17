using Xunit;

namespace SignalForge.Tests;

/// <summary>Hampel filter (ADR 0235).</summary>
public class HampelFilterTests
{
    [Fact]
    public void ZeroThresholdIsTheMedianFilter()
    {
        double[] x = [3.0, -1.0, 4.0, 1.0, -5.0, 9.0, 2.0];
        Assert.Equal(Dsp.MedianFilter(x, 3), Dsp.HampelFilter(x, 3, 0.0));
    }
}
