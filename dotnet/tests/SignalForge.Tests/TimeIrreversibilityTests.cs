using Xunit;

namespace SignalForge.Tests;

/// <summary>Time irreversibility (ADR 0357).</summary>
public class TimeIrreversibilityTests
{
    [Fact]
    public void ASawtoothByHand()
    {
        // Increments 1, 1, −2 repeated: M2 = 2, M3 = −2.
        Assert.Equal(-1 / Math.Sqrt(2), Measurements.TimeIrreversibility([0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0]), 1e-15);
        Assert.Equal(1 / Math.Sqrt(2), Measurements.TimeIrreversibility([0.0, 2.0, 1.0, 0.0, 2.0, 1.0, 0.0]), 1e-15);
    }

    [Fact]
    public void RejectsALagPastTheEnd() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TimeIrreversibility([0.0, 1.0, 2.0], 3));
}
