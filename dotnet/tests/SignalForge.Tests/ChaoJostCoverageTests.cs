using Xunit;

namespace SignalForge.Tests;

/// <summary>The Chao-Jost coverage (ADR 0553).</summary>
public class ChaoJostCoverageTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(37.0 / 49.0, Measurements.ChaoJostCoverage([1.0, 1.0, 2.0, 3.0]), 14);

    [Fact]
    public void NoSingletons() =>
        Assert.Equal(1.0, Measurements.ChaoJostCoverage([2.0, 5.0]), 15);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChaoJostCoverage([1.0]));
}
