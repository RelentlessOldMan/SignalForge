using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hawkins-Dotson coefficient (ADR 0454).</summary>
public class HawkinsDotsonCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(2.0 / 3.0, Measurements.HawkinsDotsonCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsTwoRecordsAllOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HawkinsDotsonCoefficient([1.0, 1.0], [1.0, 1.0]));
}
