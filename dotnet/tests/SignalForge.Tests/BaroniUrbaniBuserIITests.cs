using Xunit;

namespace SignalForge.Tests;

/// <summary>The second Baroni-Urbani-Buser coefficient (ADR 0468).</summary>
public class BaroniUrbaniBuserIITests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.BaroniUrbaniBuserII([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsBothAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BaroniUrbaniBuserII([0.0, 0.0], [0.0, 0.0]));
}
