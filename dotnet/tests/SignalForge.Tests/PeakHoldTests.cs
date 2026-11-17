using Xunit;

namespace SignalForge.Tests;

/// <summary>Peak hold (ADR 0243).</summary>
public class PeakHoldTests
{
    [Fact]
    public void ImpulseHoldsThenDecays()
    {
        var x = new double[12];
        x[0] = 4;
        double[] y = Dsp.PeakHold(x, 3, 0.5);
        for (int n = 0; n < 12; n++)
            Assert.Equal(n <= 3 ? 4.0 : 4.0 * Math.Pow(0.5, n - 3), y[n]);
    }
}
