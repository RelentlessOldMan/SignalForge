using Xunit;

namespace SignalForge.Tests;

/// <summary>Yule's Q (ADR 0430).</summary>
public class YuleQTests
{
    [Fact]
    public void Uneven() =>
        Assert.Equal(1.0 / 3.0, Measurements.YuleQ([1.0, 1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.YuleQ([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]));
}
