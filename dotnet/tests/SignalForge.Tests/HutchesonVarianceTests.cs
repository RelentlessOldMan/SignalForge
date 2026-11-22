using Xunit;

namespace SignalForge.Tests;

/// <summary>Hutcheson's variance (ADR 0556).</summary>
public class HutchesonVarianceTests
{
    [Fact]
    public void HalvesAndQuarters()
    {
        double ln2 = Math.Log(2.0);
        Assert.Equal(((ln2 * ln2) + 1.0) / 16.0, Measurements.HutchesonVariance([1.0, 1.0, 2.0]), 14);
    }

    [Fact]
    public void TwoTwos() =>
        Assert.Equal(1.0 / 32.0, Measurements.HutchesonVariance([2.0, 2.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HutchesonVariance([0.0, 0.0]));
}
