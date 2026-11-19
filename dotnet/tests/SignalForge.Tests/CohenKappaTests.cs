using Xunit;

namespace SignalForge.Tests;

/// <summary>Cohen's kappa (ADR 0383).</summary>
public class CohenKappaTests
{
    [Fact]
    public void UnsharedCategory() =>
        Assert.Equal(3.0 / 11, Measurements.CohenKappa([0.0, 0.0, 1.0, 2.0], [0.0, 1.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsOneSharedLabel() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CohenKappa([1.0, 1.0], [1.0, 1.0]));
}
