using Xunit;

namespace SignalForge.Tests;

/// <summary>Multiscale entropy (ADR 0338).</summary>
public class MultiscaleEntropyTests
{
    [Fact]
    public void ScaleOneIsSampleEntropy()
    {
        double[] x = [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0, 1.5];
        Assert.Equal(Measurements.SampleEntropy(x, 1, 1.5), Measurements.MultiscaleEntropy(x, 1, 1.5, [1])[0]);
    }

    [Fact]
    public void AlternatingIsZeroAtBothScales() =>
        Assert.Equal([0.0, 0.0], Measurements.MultiscaleEntropy([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 1, 0.5, [1, 2]));

    [Fact]
    public void RejectsAZeroScale() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MultiscaleEntropy([0.0, 1.0, 0.0, 1.0], 1, 0.5, [0]));
}
