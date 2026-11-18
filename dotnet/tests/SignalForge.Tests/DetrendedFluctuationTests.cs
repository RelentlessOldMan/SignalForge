using Xunit;

namespace SignalForge.Tests;

/// <summary>Detrended fluctuation analysis (ADR 0332).</summary>
public class DetrendedFluctuationTests
{
    [Fact]
    public void AlternatingByHand()
    {
        // Profile 1, 0, 1, 0: the line 0.8 − 0.2·t leaves 0.2, −0.6, 0.6, −0.2, so F(4)² = 1/5.
        DetrendedFluctuation d = Measurements.DetrendedFluctuation([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0], [4, 8]);
        Assert.Equal(Math.Sqrt(0.2), d.Fluctuations[0], 1e-15);
        Assert.Equal([4, 8], d.Scales);
    }

    [Fact]
    public void RejectsScalesOutOfOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DetrendedFluctuation([0.0, 1.0, 3.0, 2.0, 5.0, 4.0, 1.0, 2.0], [8, 4]));
}
