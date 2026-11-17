using Xunit;

namespace SignalForge.Tests;

/// <summary>Inverse sine coefficients (ADR 0216).</summary>
public class ArcsineCoefficientTests
{
    [Fact]
    public void RoundTrips()
    {
        var k = new double[41];
        for (int i = 0; i < k.Length; i++)
            k[i] = -0.98 + (0.049 * i);
        double[] back = Dsp.ArcsineToReflection(Dsp.ReflectionToArcsine(k));
        for (int i = 0; i < k.Length; i++)
            Assert.Equal(k[i], back[i], 1e-15);
    }
}
