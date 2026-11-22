using Xunit;

namespace SignalForge.Tests;

/// <summary>The Morisita-Horn overlap (ADR 0573).</summary>
public class MorisitaHornOverlapTests
{
    [Fact]
    public void Half() =>
        Assert.Equal(2.0 / 3.0, Measurements.MorisitaHornOverlap([1.0, 1.0], [1.0, 0.0]), 14);

    [Fact]
    public void HugeValues() =>
        Assert.Equal(84.0 / 85.0, Measurements.MorisitaHornOverlap([1e300, 2e300], [1.0, 3.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MorisitaHornOverlap([0.0, 0.0], [1.0, 2.0]));
}
