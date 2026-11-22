using Xunit;

namespace SignalForge.Tests;

/// <summary>The nestedness part of the Sorensen dissimilarity (ADR 0577).</summary>
public class NestednessBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.5, Measurements.NestednessBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(3.0 / 14.0, Measurements.NestednessBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.NestednessBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.NestednessBeta([0.0, 0.0], [1.0, 2.0]));
}
