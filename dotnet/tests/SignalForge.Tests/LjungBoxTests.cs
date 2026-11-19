using Xunit;

namespace SignalForge.Tests;

/// <summary>Ljung–Box statistic (ADR 0359).</summary>
public class LjungBoxTests
{
    [Fact]
    public void AlternatingByHand()
    {
        // ρ1 = −3/4, ρ2 = 1/2: Q = 24(9/48) = 9/2, then 24(9/48 + 1/8) = 15/2.
        Assert.Equal(4.5, Measurements.LjungBox([1.0, -1.0, 1.0, -1.0], 1), 1e-14);
        Assert.Equal(7.5, Measurements.LjungBox([1.0, -1.0, 1.0, -1.0], 2), 1e-14);
    }

    [Fact]
    public void RejectsTooManyLags() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LjungBox([0.0, 1.0, 2.0], 3));
}
