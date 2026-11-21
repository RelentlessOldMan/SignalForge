using Xunit;

namespace SignalForge.Tests;

/// <summary>The Bonferroni index (ADR 0520).</summary>
public class BonferroniIndexTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(13.0 / 16.0, Measurements.BonferroniIndex([3.0, 0.0, 1.0]), 14);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(1.0, Measurements.BonferroniIndex([0.0, 0.0, 0.0, 4.0]), 14);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BonferroniIndex([5.0]));
}
