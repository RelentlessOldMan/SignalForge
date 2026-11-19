using Xunit;

namespace SignalForge.Tests;

/// <summary>The Fowlkes–Mallows index (ADR 0389).</summary>
public class FowlkesMallowsIndexTests
{
    [Fact]
    public void Quarter() =>
        Assert.Equal(0.5, Measurements.FowlkesMallowsIndex([1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsARecordWithoutAOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FowlkesMallowsIndex([1.0, 0.0], [0.0, 0.0]));
}
