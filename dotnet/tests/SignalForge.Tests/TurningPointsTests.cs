using Xunit;

namespace SignalForge.Tests;

/// <summary>Turning point test (ADR 0360).</summary>
public class TurningPointsTests
{
    [Fact]
    public void OnePeakByHand()
    {
        var got = Measurements.TurningPoints([0.0, 1.0, 0.0]);
        Assert.Equal(1, got.Count);
        Assert.Equal(1.0 / 3 / Math.Sqrt(19.0 / 90), got.Z, 1e-15);
    }

    [Fact]
    public void PlateausAreNotTurningPoints() =>
        Assert.Equal(1, Measurements.TurningPoints([0.0, 1.0, 1.0, 0.0, 2.0, 2.0, 2.0, 3.0]).Count);

    [Fact]
    public void RejectsTwoSamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TurningPoints([0.0, 1.0]));
}
