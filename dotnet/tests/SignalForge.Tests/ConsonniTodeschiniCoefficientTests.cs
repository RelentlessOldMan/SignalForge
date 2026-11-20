using Xunit;

namespace SignalForge.Tests;

/// <summary>The Consonni-Todeschini coefficient (ADR 0457).</summary>
public class ConsonniTodeschiniCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(9.0) / Math.Log(11.0), Measurements.ConsonniTodeschiniCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ConsonniTodeschiniCoefficient([1.0, 0.0], [1.0]));
}
