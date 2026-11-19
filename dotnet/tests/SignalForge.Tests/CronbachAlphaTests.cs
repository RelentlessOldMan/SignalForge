using Xunit;

namespace SignalForge.Tests;

/// <summary>Cronbach's alpha (ADR 0380).</summary>
public class CronbachAlphaTests
{
    [Fact]
    public void ThreeItems() =>
        Assert.Equal(21.0 / 29, Measurements.CronbachAlpha([[1.0, 2.0, 3.0, 4.0], [2.0, 1.0, 4.0, 3.0], [1.0, 3.0, 2.0, 4.0]]), 1e-14);

    [Fact]
    public void RejectsRaggedRows() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CronbachAlpha([[1.0, 2.0, 3.0], [1.0, 2.0]]));
}
