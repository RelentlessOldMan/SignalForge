using Xunit;

namespace SignalForge.Tests;

/// <summary>Running median filter (ADR 0234).</summary>
public class MedianFilterTests
{
    [Fact]
    public void RemovesIsolatedSpikes()
    {
        double[] x = [.. Enumerable.Range(0, 50).Select(i => i % 7 == 3 ? 100.0 : 1.0)];
        Assert.All(Dsp.MedianFilter(x, 3), v => Assert.Equal(1.0, v));
    }
}
