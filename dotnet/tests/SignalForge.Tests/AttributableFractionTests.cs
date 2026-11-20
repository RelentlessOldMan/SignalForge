using Xunit;

namespace SignalForge.Tests;

/// <summary>The attributable fraction (ADR 0485).</summary>
public class AttributableFractionTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.75, Measurements.AttributableFraction([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsThatShareNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AttributableFraction([1.0, 0.0], [0.0, 1.0]));
}
