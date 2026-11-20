using Xunit;

namespace SignalForge.Tests;

/// <summary>Faith's coefficient (ADR 0456).</summary>
public class FaithCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.FaithCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FaithCoefficient([1.0, 0.0], [1.0]));
}
