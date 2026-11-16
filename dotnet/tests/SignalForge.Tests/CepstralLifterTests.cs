using Xunit;

namespace SignalForge.Tests;

/// <summary>Cepstral liftering (conventions: Cepstral liftering; ADR 0159).</summary>
public class CepstralLifterTests
{
    [Fact]
    public void KeepsC0AndPeaksAtHalfTheLength()
    {
        double[] output = Spectral.CepstralLifter(Enumerable.Repeat(1.0, 23).ToArray());
        Assert.Equal(1.0, output[0]);
        Assert.Equal(11, Array.IndexOf(output, output.Max()));
        Assert.Equal(12.0, output[11], 1e-12);
    }
}
