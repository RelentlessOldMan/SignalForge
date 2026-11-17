using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Transfer function H1 (conventions: Transfer function (H1); ADR 0193).</summary>
public class TransferFunctionTests
{
    [Fact]
    public void FirResponseIsRecoveredFromNoise()
    {
        var rng = new Random(40);
        var x = new double[16384];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        double[] h = [0.5, 0.3, 0.1];
        var y = new double[x.Length];
        for (int n = 0; n < y.Length; n++)
        {
            for (int j = 0; j < h.Length && j <= n; j++)
                y[n] += h[j] * x[n - j];
        }
        var t = Spectral.TransferFunction(x, y, 1, nperseg: 256);
        for (int k = 0; k < t.Response.Length; k++)
        {
            Complex e = Complex.Zero;
            for (int j = 0; j < h.Length; j++)
                e += h[j] * Complex.Exp(new Complex(0, -2 * Math.PI * k * j / 256));
            Assert.True((t.Response[k] - e).Magnitude < 0.02);
        }
    }
}
