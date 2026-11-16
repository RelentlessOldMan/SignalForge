using Xunit;

namespace SignalForge.Tests;

/// <summary>Sound strength (conventions: Sound strength; ADR 0178).</summary>
public class SoundStrengthTests
{
    private static readonly double[] One = [1.0];
    private static readonly double[] Zero = [0.0];
    private static readonly double[] OneThree = [1.0, 3.0];

    [Fact]
    public void ASilentReferenceIsRejected() =>
        Assert.Throws<ArgumentException>(() => Measurements.SoundStrength(One, Zero));

    [Fact]
    public void TenTimesTheEnergyIsTenDecibels() =>
        Assert.Equal(10, Measurements.SoundStrength(OneThree, One), 1e-12);
}
