using Xunit;

namespace SignalForge.Tests;

/// <summary>Schoener's overlap of two records (ADR 0598).</summary>
public class SchoenerOverlapTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0 / 3.0, Measurements.SchoenerOverlap([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Uneven() =>
        Assert.Equal(0.2, Measurements.SchoenerOverlap([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.SchoenerOverlap([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SchoenerOverlap([0.0, 0.0], [1.0, 2.0]));
}
