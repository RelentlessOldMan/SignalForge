using Xunit;

namespace SignalForge.Tests;

/// <summary>Savage's selection ratio (ADR 0606).</summary>
public class SavageSelectionRatioTests
{
    [Fact]
    public void Uneven() =>
        Assert.Equal([2.0, 0.5, 1.0], Measurements.SavageSelectionRatio([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]));

    [Fact]
    public void OneKindUsed() =>
        Assert.Equal([4.0, 0.0], Measurements.SavageSelectionRatio([1.0, 0.0], [1.0, 3.0]));

    [Fact]
    public void OneKind() =>
        Assert.Equal([1.0], Measurements.SavageSelectionRatio([2.0], [5.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SavageSelectionRatio([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SavageSelectionRatio([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]));
}
