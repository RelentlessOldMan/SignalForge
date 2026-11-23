using Xunit;

namespace SignalForge.Tests;

/// <summary>The richness-difference part of the Ruzicka dissimilarity (ADR 0587).</summary>
public class RuzickaRichnessDifferenceTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(2.0 / 3.0, Measurements.RuzickaRichnessDifference([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Huge() =>
        Assert.Equal(0.5, Measurements.RuzickaRichnessDifference([1.5e308, 0.0], [1.5e308, 1.5e308]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.RuzickaRichnessDifference([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RuzickaRichnessDifference([0.0, 0.0], [1.0, 2.0]));
}
