using Xunit;

namespace SignalForge.Tests;

/// <summary>The pattern difference (ADR 0474).</summary>
public class PatternDifferenceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.04, Measurements.PatternDifference([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PatternDifference([0.0, 1.0], [1.0]));
}
