using Xunit;

namespace SignalForge.Tests;

/// <summary>Manly's alpha (ADR 0602).</summary>
public class ManlyAlphaTests
{
    [Fact]
    public void EvenUse() =>
        Assert.Equal([0.75, 0.25], Measurements.ManlyAlpha([1.0, 1.0], [1.0, 3.0]));

    [Fact]
    public void Uneven()
    {
        double[] got = Measurements.ManlyAlpha([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]);
        Assert.Equal(4.0 / 7.0, got[0], 15);
        Assert.Equal(1.0 / 7.0, got[1], 15);
        Assert.Equal(2.0 / 7.0, got[2], 15);
    }

    [Fact]
    public void OneKindUsed() =>
        Assert.Equal([1.0, 0.0], Measurements.ManlyAlpha([1.0, 0.0], [1.0, 3.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ManlyAlpha([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ManlyAlpha([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]));
}
