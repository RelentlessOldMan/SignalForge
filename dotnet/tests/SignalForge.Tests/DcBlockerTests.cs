using Xunit;

namespace SignalForge.Tests;

/// <summary>DC blocker (ADR 0236).</summary>
public class DcBlockerTests
{
    [Fact]
    public void RemovesAnOffset()
    {
        double[] x = [.. Enumerable.Range(0, 20000).Select(n => 3.0 + Math.Sin(2 * Math.PI * 0.05 * n))];
        double[] y = Dsp.DcBlocker(x, 0.995);
        Assert.True(Math.Abs(y.Skip(10000).Average()) < 1e-3);
    }
}
