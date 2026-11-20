using Xunit;

namespace SignalForge.Tests;

/// <summary>The fourth Sokal-Sneath coefficient (ADR 0459).</summary>
public class SokalSneathIVTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.8, Measurements.SokalSneathIV([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SokalSneathIV([1.0, 1.0], [1.0, 0.0]));
}
