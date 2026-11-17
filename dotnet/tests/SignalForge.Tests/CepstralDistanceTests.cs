using Xunit;

namespace SignalForge.Tests;

/// <summary>Cepstral distance between AR models (ADR 0218).</summary>
public class CepstralDistanceTests
{
    [Fact]
    public void IsZeroForEqualModelsAndSymmetric()
    {
        double[] a = Dsp.ReflectionToLpc([0.6, -0.4, 0.3]);
        double[] b = Dsp.ReflectionToLpc([-0.5, 0.2]);
        Assert.Equal(0, Dsp.CepstralDistance(a, a, 12), 1e-15);
        Assert.Equal(Dsp.CepstralDistance(a, b, 12), Dsp.CepstralDistance(b, a, 12), 1e-15);
    }
}
