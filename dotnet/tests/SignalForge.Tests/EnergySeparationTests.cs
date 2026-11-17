using Xunit;

namespace SignalForge.Tests;

/// <summary>Energy separation (conventions: Energy separation; ADR 0189).</summary>
public class EnergySeparationTests
{
    [Fact]
    public void ASlowAmToneFollowsItsEnvelope()
    {
        var x = new double[400];
        var env = new double[400];
        for (int n = 0; n < x.Length; n++)
        {
            env[n] = 1 + 0.3 * Math.Cos(2 * Math.PI * n / 400);
            x[n] = env[n] * Math.Cos(0.5 * n);
        }
        var r = Measurements.EnergySeparation(x, 1);
        for (int i = 0; i < r.Amplitude.Length; i++)
        {
            Assert.True(Math.Abs(r.Amplitude[i] / env[i + 2] - 1) < 1e-3);
            Assert.True(Math.Abs(r.Frequency[i] * 2 * Math.PI / 0.5 - 1) < 1e-3);
        }
    }
}
