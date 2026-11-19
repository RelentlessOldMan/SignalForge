using Xunit;

namespace SignalForge.Tests;

/// <summary>Buishand range test (ADR 0367).</summary>
public class BuishandRangeTests
{
    [Fact]
    public void StepByHand()
    {
        // S = −1, −2, −1, 0 with σ = 1.
        var got = Measurements.BuishandRange([0.0, 0.0, 2.0, 2.0]);
        Assert.Equal(2.0, got.Q);
        Assert.Equal(2.0, got.R);
        Assert.Equal(1, got.Index);
    }

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BuishandRange([1.0, 1.0]));
}
