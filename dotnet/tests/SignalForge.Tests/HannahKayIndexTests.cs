using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hannah-Kay index (ADR 0527).</summary>
public class HannahKayIndexTests
{
    [Fact]
    public void RampAtTwo() =>
        Assert.Equal(10.0 / 3.0, Measurements.HannahKayIndex([4.0, 1.0, 3.0, 2.0], 2.0), 13);

    [Fact]
    public void EqualAtOne() =>
        Assert.Equal(4.0, Measurements.HannahKayIndex([2.0, 2.0, 2.0, 2.0], 1.0), 13);

    [Fact]
    public void RejectsAZeroAlpha() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HannahKayIndex([1.0, 2.0], 0.0));
}
