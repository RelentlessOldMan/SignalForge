using Xunit;

namespace SignalForge.Tests;

/// <summary>The Ruzicka similarity of two records (ADR 0580).</summary>
public class RuzickaSimilarityTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0 / 3.0, Measurements.RuzickaSimilarity([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Huge() =>
        Assert.Equal(0.5, Measurements.RuzickaSimilarity([1.5e308, 1.5e308], [1.5e308, 0.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.RuzickaSimilarity([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RuzickaSimilarity([0.0, 0.0], [1.0, 2.0]));
}
