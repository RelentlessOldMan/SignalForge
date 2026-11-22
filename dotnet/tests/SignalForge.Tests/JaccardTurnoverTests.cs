using Xunit;

namespace SignalForge.Tests;

/// <summary>The turnover part of the Jaccard dissimilarity (ADR 0578).</summary>
public class JaccardTurnoverTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.JaccardTurnover([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(2.0 / 3.0, Measurements.JaccardTurnover([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.JaccardTurnover([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JaccardTurnover([0.0, 0.0], [1.0, 2.0]));
}
