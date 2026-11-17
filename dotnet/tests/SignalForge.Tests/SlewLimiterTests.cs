using Xunit;

namespace SignalForge.Tests;

/// <summary>Slew-rate limiter (ADR 0242).</summary>
public class SlewLimiterTests
{
    [Fact]
    public void StepClimbsAtTheRiseRate()
    {
        double[] y = Dsp.SlewLimiter([.. Enumerable.Repeat(3.0, 8)], 0.5, 1.0);
        for (int n = 0; n < 8; n++)
            Assert.Equal(Math.Min(3.0, (n + 1) * 0.5), y[n]);
    }
}
