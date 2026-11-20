using Xunit;

namespace SignalForge.Tests;

/// <summary>Goodman and Kruskal's lambda (ADR 0447).</summary>
public class GoodmanKruskalLambdaTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.GoodmanKruskalLambda([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsTwoConstantRecords() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GoodmanKruskalLambda([1.0, 1.0], [0.0, 0.0]));
}
