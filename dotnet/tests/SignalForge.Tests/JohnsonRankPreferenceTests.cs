using Xunit;

namespace SignalForge.Tests;

/// <summary>Johnson's rank preference index (ADR 0608).</summary>
public class JohnsonRankPreferenceTests
{
    [Fact]
    public void Reversed() =>
        Assert.Equal([2.0, 0.0, -2.0], Measurements.JohnsonRankPreference([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal([-2.5, 0.5, -1.0, 3.0], Measurements.JohnsonRankPreference([2.0, 1.0, 1.0, 0.0], [1.0, 2.0, 1.0, 4.0]));

    [Fact]
    public void OneKind() =>
        Assert.Equal([0.0], Measurements.JohnsonRankPreference([2.0], [5.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JohnsonRankPreference([1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JohnsonRankPreference([0.0, 0.0], [1.0, 1.0]));
}
