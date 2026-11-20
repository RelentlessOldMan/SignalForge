using Xunit;

namespace SignalForge.Tests;

/// <summary>The first Kulczynski coefficient (ADR 0462).</summary>
public class KulczynskiITests
{
    [Fact]
    public void Square() =>
        Assert.Equal(2.0, Measurements.KulczynskiI([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsThatAgreeEverywhere() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KulczynskiI([1.0, 0.0], [1.0, 0.0]));
}
