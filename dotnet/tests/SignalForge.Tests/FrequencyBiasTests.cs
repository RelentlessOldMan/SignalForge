using Xunit;

namespace SignalForge.Tests;

/// <summary>The frequency bias (ADR 0488).</summary>
public class FrequencyBiasTests
{
    [Fact]
    public void Uneven() =>
        Assert.Equal(5.0 / 3.0, Measurements.FrequencyBias([1, 1, 0, 0, 0, 1, 0], [1, 0, 1, 1, 1, 1, 0]), 15);

    [Fact]
    public void RejectsTruthWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FrequencyBias([0.0, 0.0], [1.0, 0.0]));
}
