using Xunit;

namespace SignalForge.Tests;

/// <summary>Mountford's coefficient (ADR 0452).</summary>
public class MountfordCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.8, Measurements.MountfordCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsThatAgreeEverywhere() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MountfordCoefficient([1.0, 0.0], [1.0, 0.0]));
}
