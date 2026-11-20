using Xunit;

namespace SignalForge.Tests;

/// <summary>The third Sokal-Sneath coefficient (ADR 0461).</summary>
public class SokalSneathIIITests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4.0, Measurements.SokalSneathIII([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsThatAgreeEverywhere() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SokalSneathIII([1.0, 0.0], [1.0, 0.0]));
}
