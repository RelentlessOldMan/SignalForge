using Xunit;

namespace SignalForge.Tests;

/// <summary>The Rényi divergence (ADR 0413).</summary>
public class RenyiDivergenceTests
{
    [Fact]
    public void OrderTwo() =>
        Assert.Equal(Math.Log(1.25), Measurements.RenyiDivergence([3.0, 1.0], [1.0, 1.0], 2.0), 1e-15);

    [Fact]
    public void RejectsOrderOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RenyiDivergence([1.0, 2.0], [2.0, 1.0], 1.0));
}
