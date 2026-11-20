using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of Yule's Q (ADR 0495).</summary>
public class YuleQStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(16.0 * Math.Sqrt(10.0) / 289.0, Measurements.YuleQStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsATableWithAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.YuleQStandardError([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
