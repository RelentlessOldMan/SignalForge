using Xunit;

namespace SignalForge.Tests;

/// <summary>The Jensen–Shannon divergence (ADR 0408).</summary>
public class JsDivergenceTests
{
    [Fact]
    public void Disjoint() =>
        Assert.Equal(Math.Log(2.0), Measurements.JsDivergence([1.0, 0.0], [0.0, 3.0]), 1e-15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JsDivergence([1.0, 1.0], [1.0]));
}
