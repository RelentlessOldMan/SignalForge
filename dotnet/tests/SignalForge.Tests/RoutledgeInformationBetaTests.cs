using Xunit;

namespace SignalForge.Tests;

/// <summary>Routledge's information beta of two presence records (ADR 0595).</summary>
public class RoutledgeInformationBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.5 * Math.Log(2.0) - 0.75 * Math.Log(3.0), Measurements.RoutledgeInformationBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(Math.Log(7.0) - 4.0 * Math.Log(2.0) / 7.0 - 5.0 * Math.Log(5.0) / 7.0, Measurements.RoutledgeInformationBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 14);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(Math.Log(2.0), Measurements.RoutledgeInformationBeta([1.0, 0.0], [0.0, 1.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RoutledgeInformationBeta([0.0, 0.0], [1.0, 2.0]));
}
