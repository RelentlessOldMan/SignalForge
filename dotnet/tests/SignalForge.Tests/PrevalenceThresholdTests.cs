using Xunit;

namespace SignalForge.Tests;

/// <summary>The prevalence threshold (ADR 0487).</summary>
public class PrevalenceThresholdTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(1.0 / 3.0, Measurements.PrevalenceThreshold([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsEqualRates() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PrevalenceThreshold([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
