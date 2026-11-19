using Xunit;

namespace SignalForge.Tests;

/// <summary>Fisher information (ADR 0351).</summary>
public class FisherInformationTests
{
    [Fact]
    public void AFlatSpectrumIsZero() =>
        Assert.Equal(0.0, Measurements.FisherInformation([1.0, 0.0, -1.0, 0.0, 1.0], 2), 1e-15);

    [Fact]
    public void ARankOneEmbeddingIsOne()
    {
        double[] x = [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0];
        Assert.Equal(1.0, Measurements.FisherInformation(x, 4), 1e-12);
    }

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FisherInformation([0.0, 0.0, 0.0, 0.0], 2));
}
