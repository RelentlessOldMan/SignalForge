using Xunit;

namespace SignalForge.Tests;

/// <summary>Yule's Y (ADR 0431).</summary>
public class YuleYTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.YuleY([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.YuleY([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]));
}
