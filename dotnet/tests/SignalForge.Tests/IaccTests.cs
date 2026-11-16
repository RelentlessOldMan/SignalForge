using Xunit;

namespace SignalForge.Tests;

/// <summary>Interaural cross-correlation (conventions: Interaural cross-correlation; ADR 0174).</summary>
public class IaccTests
{
    [Fact]
    public void ADelayedCopyWithinOneMsGivesOne()
    {
        var rng = new Random(11);
        var left = new double[2000];
        var right = new double[2000];
        for (int n = 0; n < left.Length; n++)
            left[n] = rng.NextDouble() - 0.5;
        for (int n = 20; n < right.Length; n++)
            right[n] = 0.3 * left[n - 20];
        Assert.Equal(1.0, Measurements.Iacc(left, right, 48000), 0.02);
        Assert.True(Measurements.Iacc(left, right, 48000, 0.0002) < 0.2);
    }
}
