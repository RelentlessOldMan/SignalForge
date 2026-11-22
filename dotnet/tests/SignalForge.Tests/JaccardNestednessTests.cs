using Xunit;

namespace SignalForge.Tests;

/// <summary>The nestedness part of the Jaccard dissimilarity (ADR 0579).</summary>
public class JaccardNestednessTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(2.0 / 3.0, Measurements.JaccardNestedness([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Uneven() =>
        Assert.Equal(1.0 / 6.0, Measurements.JaccardNestedness([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.JaccardNestedness([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JaccardNestedness([0.0, 0.0], [1.0, 2.0]));
}
