using Xunit;

namespace SignalForge.Tests;

/// <summary>Cliff's delta (ADR 0400).</summary>
public class CliffDeltaTests
{
    [Fact]
    public void HandTwo() =>
        Assert.Equal(0.5, Measurements.CliffDelta([2.0, 4.0, 6.0, 8.0], [1.0, 5.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CliffDelta([], [1.0]));
}
