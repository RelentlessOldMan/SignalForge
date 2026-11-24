using Xunit;

namespace SignalForge.Tests;

/// <summary>Vanderploeg and Scavia's relativized electivity (ADR 0605).</summary>
public class VanderploegScaviaElectivityTests
{
    [Fact]
    public void Uneven()
    {
        double[] got = Measurements.VanderploegScaviaElectivity([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]);
        Assert.Equal(5.0 / 19.0, got[0], 15);
        Assert.Equal(-0.4, got[1], 15);
        Assert.Equal(-1.0 / 13.0, got[2], 15);
    }

    [Fact]
    public void UnusedKind() =>
        Assert.Equal(-1.0, Measurements.VanderploegScaviaElectivity([1.0, 0.0], [1.0, 3.0])[1]);

    [Fact]
    public void OneKind() =>
        Assert.Equal([0.0], Measurements.VanderploegScaviaElectivity([2.0], [5.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.VanderploegScaviaElectivity([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.VanderploegScaviaElectivity([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]));
}
