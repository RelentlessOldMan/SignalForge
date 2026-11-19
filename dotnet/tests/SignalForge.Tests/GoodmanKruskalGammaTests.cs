using Xunit;

namespace SignalForge.Tests;

/// <summary>Goodman and Kruskal's gamma (ADR 0377).</summary>
public class GoodmanKruskalGammaTests
{
    [Fact]
    public void TiesDropped() =>
        Assert.Equal(-1.0 / 3, Measurements.GoodmanKruskalGamma([1.0, 1.0, 2.0, 3.0], [1.0, 2.0, 2.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GoodmanKruskalGamma([1.0, 2.0, 3.0], [1.0, 1.0, 1.0]));
}
