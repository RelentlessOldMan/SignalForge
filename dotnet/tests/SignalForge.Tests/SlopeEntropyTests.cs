using Xunit;

namespace SignalForge.Tests;

/// <summary>Slope entropy (ADR 0347).</summary>
public class SlopeEntropyTests
{
    [Fact]
    public void ARampIsZero() =>
        Assert.Equal(0.0, Measurements.SlopeEntropy([0.0, 0.5, 1.0, 1.5, 2.0], 3), 1e-15);

    [Fact]
    public void TwoSymbolsByHand()
    {
        // Steps +2 (> γ), 0, +2, 0: m = 2 gives two patterns, 2 and 2 times.
        Assert.Equal(Math.Log(2), Measurements.SlopeEntropy([0.0, 2.0, 2.0, 4.0, 4.0], 2), 1e-15);
    }

    [Fact]
    public void RejectsDeltaAboveGamma() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SlopeEntropy([0.0, 1.0, 2.0], 2, 0.5, 1.0));
}
