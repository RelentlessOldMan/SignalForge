using Xunit;

namespace SignalForge.Tests;

/// <summary>Fleiss' kappa (ADR 0382).</summary>
public class FleissKappaTests
{
    [Fact]
    public void Split() =>
        Assert.Equal(-1.0, Measurements.FleissKappa([[1.0, 1.0], [1.0, 1.0]]), 1e-15);

    [Fact]
    public void RejectsRaggedRows() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FleissKappa([[1.0, 2.0, 0.0], [1.0, 2.0]]));
}
