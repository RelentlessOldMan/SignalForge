using Xunit;

namespace SignalForge.Tests;

/// <summary>Glass's delta (ADR 0399).</summary>
public class GlassDeltaTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(8.0, Measurements.GlassDelta([10.0, 20.0, 30.0], [2.0, 4.0, 6.0]), 1e-15);

    [Fact]
    public void RejectsAControlWithoutSpread() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GlassDelta([1.0, 2.0], [2.0, 2.0]));
}
