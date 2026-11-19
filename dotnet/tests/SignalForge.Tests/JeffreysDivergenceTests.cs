using Xunit;

namespace SignalForge.Tests;

/// <summary>The Jeffreys divergence (ADR 0414).</summary>
public class JeffreysDivergenceTests
{
    [Fact]
    public void Coin() =>
        Assert.Equal(Math.Log(3.0) / 4.0, Measurements.JeffreysDivergence([3.0, 1.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAZeroInOnlyOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JeffreysDivergence([1.0, 0.0], [1.0, 1.0]));
}
