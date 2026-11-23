using Xunit;

namespace SignalForge.Tests;

/// <summary>Podani's richness-difference part of the Jaccard dissimilarity (ADR 0585).</summary>
public class PodaniRichnessDifferenceTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(2.0 / 3.0, Measurements.PodaniRichnessDifference([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Uneven() =>
        Assert.Equal(0.5, Measurements.PodaniRichnessDifference([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.PodaniRichnessDifference([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PodaniRichnessDifference([0.0, 0.0], [1.0, 2.0]));
}
