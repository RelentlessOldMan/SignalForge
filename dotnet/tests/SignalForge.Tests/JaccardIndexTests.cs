using Xunit;

namespace SignalForge.Tests;

/// <summary>The Jaccard index (ADR 0388).</summary>
public class JaccardIndexTests
{
    [Fact]
    public void Overlap() =>
        Assert.Equal(0.4, Measurements.JaccardIndex([1.0, 1.0, 1.0, 0.0, 0.0], [1.0, 1.0, 0.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptyUnion() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JaccardIndex([0.0, 0.0], [0.0, 0.0]));
}
