using Xunit;

namespace SignalForge.Tests;

/// <summary>Cepstrum to prediction filter (ADR 0222).</summary>
public class CepstrumToLpcTests
{
    [Fact]
    public void InvertsLpcCepstrum()
    {
        double[] a = Dsp.ReflectionToLpc([0.4, -0.3, 0.2, 0.1, -0.35]);
        double[] back = Dsp.CepstrumToLpc(Dsp.LpcCepstrum(a, 0.7, 10), a.Length - 1);
        for (int j = 0; j < a.Length; j++)
            Assert.Equal(a[j], back[j], 1e-12);
    }
}
