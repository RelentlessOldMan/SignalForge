using Xunit;

namespace SignalForge.Tests;

/// <summary>Bartels rank test (ADR 0363).</summary>
public class BartelsRankTestTests
{
    [Fact]
    public void ThreeByHand()
    {
        // Ranks 2, 1, 3: ratio 5/2; variance 1/2.
        var got = Measurements.BartelsRankTest([5.0, -2.0, 7.0]);
        Assert.Equal(2.5, got.Ratio, 1e-15);
        Assert.Equal(0.5 / Math.Sqrt(0.5), got.Z, 1e-15);
    }

    [Fact]
    public void TiesTakeTheMeanRank() =>
        Assert.Equal(2.5, Measurements.BartelsRankTest([1.0, 1.0, 3.0, 0.0]).Ratio, 1e-15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BartelsRankTest([1.0, 1.0, 1.0]));
}
