using Xunit;

namespace SignalForge.Tests;

/// <summary>Ivlev's electivity (ADR 0603).</summary>
public class IvlevElectivityTests
{
    [Fact]
    public void EvenUse()
    {
        double[] got = Measurements.IvlevElectivity([1.0, 1.0], [1.0, 3.0]);
        Assert.Equal(1.0 / 3.0, got[0], 15);
        Assert.Equal(-0.2, got[1], 15);
    }

    [Fact]
    public void Uneven()
    {
        double[] got = Measurements.IvlevElectivity([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]);
        Assert.Equal(1.0 / 3.0, got[0], 15);
        Assert.Equal(-1.0 / 3.0, got[1], 15);
        Assert.Equal(0.0, got[2]);
    }

    [Fact]
    public void UnusedKind() =>
        Assert.Equal(-1.0, Measurements.IvlevElectivity([1.0, 0.0], [1.0, 3.0])[1]);

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IvlevElectivity([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsUnderflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IvlevElectivity([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]));
}
