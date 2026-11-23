using Xunit;

namespace SignalForge.Tests;

/// <summary>Podani's replacement part of the Jaccard dissimilarity (ADR 0584).</summary>
public class PodaniReplacementTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.PodaniReplacement([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(1.0 / 3.0, Measurements.PodaniReplacement([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.PodaniReplacement([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PodaniReplacement([0.0, 0.0], [1.0, 2.0]));
}
