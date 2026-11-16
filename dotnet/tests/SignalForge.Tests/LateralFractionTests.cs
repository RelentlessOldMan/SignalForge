using Xunit;

namespace SignalForge.Tests;

/// <summary>Lateral energy fraction (conventions: Lateral energy fraction; ADR 0175).</summary>
public class LateralFractionTests
{
    [Fact]
    public void AHalfScaledEightGivesAQuarterOfTheLateWindow()
    {
        var omni = new double[4800];
        var eight = new double[4800];
        var rng = new Random(13);
        omni[0] = 3;
        for (int n = 240; n < omni.Length; n++)
        {
            omni[n] = rng.NextDouble() - 0.5;
            eight[n] = 0.5 * omni[n];
        }
        double late = 0, all = 9;
        for (int n = 240; n < 3840; n++)
        {
            late += omni[n] * omni[n];
            all += omni[n] * omni[n];
        }
        Assert.Equal(0.25 * late / all, Measurements.LateralFraction(omni, eight, 48000), 1e-12);
    }

    [Fact]
    public void StartAtOrAboveStopIsRejected() =>
        Assert.Throws<ArgumentOutOfRangeException>(() => Measurements.LateralFraction([1.0, 1.0], [1.0, 1.0], 100, 0.02, 0.02));
}
