using Xunit;

namespace SignalForge.Tests;

/// <summary>Jacobs' selectivity index (ADR 0604).</summary>
public class JacobsSelectivityTests
{
    [Fact]
    public void Uneven()
    {
        double[] got = Measurements.JacobsSelectivity([2.0, 1.0, 1.0], [1.0, 2.0, 1.0]);
        Assert.Equal(0.5, got[0], 15);
        Assert.Equal(-0.5, got[1], 15);
        Assert.Equal(0.0, got[2]);
    }

    [Fact]
    public void OnlyKindUsed() =>
        Assert.Equal([1.0, -1.0], Measurements.JacobsSelectivity([1.0, 0.0], [1.0, 3.0]));

    [Fact]
    public void OneKind() =>
        Assert.Equal([0.0], Measurements.JacobsSelectivity([2.0], [5.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JacobsSelectivity([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsUnderflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JacobsSelectivity([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]));
}
