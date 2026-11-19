using Xunit;

namespace SignalForge.Tests;

/// <summary>Hoeffding's D (ADR 0374).</summary>
public class HoeffdingDTests
{
    [Fact]
    public void MonotoneFive() =>
        Assert.Equal(1.0, Measurements.HoeffdingD([1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 8.0, 16.0, 32.0]), 1e-15);

    [Fact]
    public void RejectsFourSamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HoeffdingD([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]));
}
