using Xunit;

namespace SignalForge.Tests;

/// <summary>DCT-II and its inverse (conventions: DCT-II; ADR 0156).</summary>
public class DctTests
{
    [Theory]
    [InlineData(1, true)]
    [InlineData(3, true)]
    [InlineData(16, true)]
    [InlineData(25, true)]
    [InlineData(1, false)]
    [InlineData(7, false)]
    [InlineData(16, false)]
    public void RoundTrip(int n, bool orthonormal)
    {
        var rng = new Random(n);
        double[] x = Enumerable.Range(0, n).Select(_ => rng.NextDouble() - 0.5).ToArray();
        double[] back = Spectral.Idct(Spectral.Dct(x, orthonormal), orthonormal);
        for (int i = 0; i < n; i++)
            Assert.Equal(x[i], back[i], 1e-12);
    }

    [Fact]
    public void OrthonormalMatrixIsOrthogonal()
    {
        const int N = 13;
        var cols = new double[N][];
        for (int j = 0; j < N; j++)
        {
            var e = new double[N];
            e[j] = 1;
            cols[j] = Spectral.Dct(e);
        }
        for (int a = 0; a < N; a++)
        {
            for (int b = 0; b < N; b++)
            {
                double dot = 0;
                for (int j = 0; j < N; j++)
                    dot += cols[j][a] * cols[j][b];
                Assert.Equal(a == b ? 1.0 : 0.0, dot, 1e-12);
            }
        }
    }
}
