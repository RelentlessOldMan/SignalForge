using Xunit;

namespace SignalForge.Tests;

/// <summary>The Brier score (ADR 0391).</summary>
public class BrierScoreTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(11.0 / 32, Measurements.BrierScore([1.0, 0.0, 1.0, 0.0], [0.75, 0.25, 0.5, 1.0]), 1e-15);

    [Fact]
    public void RejectsNaNProbability() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrierScore([1.0, 0.0], [0.5, double.NaN]));
}
