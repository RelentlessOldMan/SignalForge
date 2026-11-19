using Xunit;

namespace SignalForge.Tests;

/// <summary>Largest Lyapunov exponent (ADR 0354).</summary>
public class LargestLyapunovTests
{
    [Fact]
    public void TheFirstStepByHand()
    {
        // P = 4 points 0, 1, 1.25, 3 pair with 1, 2, 1, 2: distances 1, 0.25, 0.25, 1.75.
        var got = Measurements.LargestLyapunov([0.0, 1.0, 1.25, 3.0, 3.5, 7.0], 1, 2);
        double expected = (Math.Log(1) + Math.Log(0.25) + Math.Log(0.25) + Math.Log(1.75)) / 4;
        Assert.Equal(expected, got.Divergence[0], 1e-15);
        Assert.Equal(3, got.Divergence.Length);
    }

    [Fact]
    public void TheLogisticMapIsNearLn2()
    {
        var x = new double[1500];
        x[0] = 0.2345;
        for (int i = 1; i < x.Length; i++)
            x[i] = 4 * x[i - 1] * (1 - x[i - 1]);
        Assert.InRange(Measurements.LargestLyapunov(x, 2, 4, theiler: 5).Exponent, Math.Log(2) - 0.15, Math.Log(2) + 0.15);
    }

    [Fact]
    public void RejectsTooFewPoints() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LargestLyapunov([0.0, 1.0, 2.0, 3.0], 1, 1, theiler: 1));
}
