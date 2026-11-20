using Xunit;

namespace SignalForge.Tests;

/// <summary>The fifth Sokal-Sneath coefficient (ADR 0460).</summary>
public class SokalSneathVTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.64, Measurements.SokalSneathV([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SokalSneathV([1.0, 1.0], [1.0, 0.0]));
}
