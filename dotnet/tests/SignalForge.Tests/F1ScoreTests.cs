using Xunit;

namespace SignalForge.Tests;

/// <summary>The F1 score (ADR 0386).</summary>
public class F1ScoreTests
{
    [Fact]
    public void HalfAndTwoThirds() =>
        Assert.Equal(4.0 / 7, Measurements.F1Score([1.0, 1.0, 1.0, 0.0, 0.0], [1.0, 1.0, 0.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsNoPositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.F1Score([0.0, 0.0], [0.0, 0.0]));
}
