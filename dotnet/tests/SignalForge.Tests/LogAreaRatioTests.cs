using Xunit;

namespace SignalForge.Tests;

/// <summary>Log-area ratios (ADR 0215).</summary>
public class LogAreaRatioTests
{
    [Fact]
    public void RoundTrips()
    {
        var k = new double[41];
        for (int i = 0; i < k.Length; i++)
            k[i] = -0.98 + (0.049 * i);
        double[] back = Dsp.LarToReflection(Dsp.ReflectionToLar(k));
        for (int i = 0; i < k.Length; i++)
            Assert.Equal(k[i], back[i], 1e-14);
    }
}
