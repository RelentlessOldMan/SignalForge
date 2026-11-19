using Xunit;

namespace SignalForge.Tests;

/// <summary>Youden's J (ADR 0387).</summary>
public class YoudenJTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(5.0 / 12, Measurements.YoudenJ([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 1e-15);

    [Fact]
    public void RejectsAMissingTrueClass() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.YoudenJ([1.0, 1.0], [1.0, 0.0]));
}
