using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Sliding DFT (ADR 0231).</summary>
public class SlidingDftTests
{
    [Fact]
    public void EqualsFftOfEachFullWindow()
    {
        var rng = new Random(10);
        double[] x = [.. Enumerable.Range(0, 300).Select(_ => rng.NextDouble() - 0.5)];
        int n = 16, k = 5;
        Complex[] s = Spectral.SlidingDft(x, n, k);
        for (int i = n - 1; i < 300; i++)
        {
            Complex want = Spectral.Fft(x.AsSpan(i - n + 1, n))[k];
            Assert.True(Complex.Abs(s[i] - want) < 1e-10, $"sample {i}");
        }
    }
}
