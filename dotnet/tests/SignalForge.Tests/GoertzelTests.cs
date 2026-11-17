using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Goertzel (ADR 0224).</summary>
public class GoertzelTests
{
    [Fact]
    public void EqualsFftOnBins()
    {
        var rng = new Random(3);
        double[] x = [.. Enumerable.Range(0, 64).Select(_ => rng.NextDouble() - 0.5)];
        Complex[] fft = Spectral.Fft(x);
        Complex[] g = Spectral.Goertzel(x, 64.0, [.. Enumerable.Range(0, 64).Select(k => (double)k)]);
        for (int k = 0; k < 64; k++)
            Assert.True(Complex.Abs(fft[k] - g[k]) < 1e-11, $"bin {k}");
    }
}
