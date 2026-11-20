using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of Yule's Y (ADR 0496).</summary>
public class YuleYStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(2.0 * Math.Sqrt(10.0) / 25.0, Measurements.YuleYStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsATableWithAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.YuleYStandardError([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
