using Xunit;

namespace SignalForge.Tests;

/// <summary>The Zenga index (ADR 0521).</summary>
public class ZengaIndexTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(11.0 / 12.0, Measurements.ZengaIndex([3.0, 0.0, 1.0]), 14);

    [Fact]
    public void Ramp() =>
        Assert.Equal(73.0 / 126.0, Measurements.ZengaIndex([4.0, 1.0, 3.0, 2.0]), 14);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ZengaIndex([5.0]));
}
