using Xunit;

namespace SignalForge.Tests;

/// <summary>Transfer function H2 (conventions: Transfer function (H2); ADR 0195).</summary>
public class TransferFunctionH2Tests
{
    [Fact]
    public void H1OverH2IsTheCoherence()
    {
        var rng = new Random(43);
        var x = new double[4096];
        var y = new double[4096];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        for (int n = 0; n < y.Length; n++)
            y[n] = 0.6 * x[n] + (n >= 1 ? 0.2 * x[n - 1] : 0) + 0.3 * (rng.NextDouble() - 0.5);
        var h1 = Spectral.TransferFunction(x, y, 1, nperseg: 128).Response;
        var h2 = Spectral.TransferFunctionH2(x, y, 1, nperseg: 128).Response;
        var c = Spectral.Coherence(x, y, 1, nperseg: 128).Values;
        for (int k = 0; k < c.Length; k++)
        {
            var r = h1[k] / h2[k];
            Assert.Equal(c[k], r.Real, 1e-12);
            Assert.Equal(0, r.Imaginary, 1e-12);
        }
    }
}
