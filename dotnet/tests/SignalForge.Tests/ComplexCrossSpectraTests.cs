using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Coherence, H1 and H2 of complex input (conventions: Complex coherence and transfer
/// functions; ADR 0197).</summary>
public class ComplexCrossSpectraTests
{
    [Fact]
    public void ComplexChannelAndShiftedFrequencies()
    {
        var rng = new Random(45);
        var x = new Complex[2048];
        for (int n = 0; n < x.Length; n++)
            x[n] = new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5);
        Complex h0 = 0.7, h1 = new(0, 0.2);
        var y = new Complex[x.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = h0 * x[n] + (n >= 1 ? h1 * x[n - 1] : Complex.Zero);
        var r = Spectral.TransferFunction(x, y, 8, nperseg: 64);
        var w = Spectral.WelchPsd(x, 8, nperseg: 64);
        Assert.Equal(w.Frequencies, r.Frequencies);
        var c = Spectral.Coherence(x, y, 8, nperseg: 64).Values;
        var r2 = Spectral.TransferFunctionH2(x, y, 8, nperseg: 64).Response;
        for (int k = 0; k < c.Length; k++)
        {
            var expected = h0 + h1 * Complex.Exp(new Complex(0, -2 * Math.PI * r.Frequencies[k] / 8));
            Assert.True((r.Response[k] - expected).Magnitude < 0.05);
            var ratio = r.Response[k] / r2[k];
            Assert.Equal(c[k], ratio.Real, 1e-12);
        }
    }
}
