using Xunit;

namespace SignalForge.Tests;

/// <summary>The total variation distance (ADR 0411).</summary>
public class TotalVariationDistanceTests
{
    [Fact]
    public void Half() =>
        Assert.Equal(0.5, Measurements.TotalVariationDistance([1.0, 0.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TotalVariationDistance([1.0], [1.0, 1.0]));
}
