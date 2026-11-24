using Xunit;

namespace SignalForge.Tests;

/// <summary>Strauss' linear selection index (ADR 0607).</summary>
public class StraussSelectionTests
{
    [Fact]
    public void Uneven() =>
        Assert.Equal([0.25, -0.25, 0.0], Measurements.StraussSelection([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]));

    [Fact]
    public void OneKindUsed() =>
        Assert.Equal([0.75, -0.75], Measurements.StraussSelection([1.0, 0.0], [1.0, 3.0]));

    [Fact]
    public void OneKind() =>
        Assert.Equal([0.0], Measurements.StraussSelection([2.0], [5.0]));

    [Fact]
    public void SmallShare() =>
        Assert.Equal(1.0 / 3.0, Measurements.StraussSelection([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0])[1], 15);

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.StraussSelection([1.0, 1.0], [1.0, 0.0]));
}
