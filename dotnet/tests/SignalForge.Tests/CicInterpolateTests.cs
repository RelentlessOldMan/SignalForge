using Xunit;

namespace SignalForge.Tests;

/// <summary>CIC interpolator (ADR 0230).</summary>
public class CicInterpolateTests
{
    [Fact]
    public void MatchesCombIntegratorStructure()
    {
        var rng = new Random(9);
        double[] x = [.. Enumerable.Range(0, 60).Select(_ => (double)rng.Next(-100, 100))];
        int r = 4, n = 3, m = 2;
        double[] s = [.. x];
        for (int st = 0; st < n; st++)
        {
            for (int i = s.Length - 1; i >= m; i--)
                s[i] -= s[i - m];
        }
        var u = new double[x.Length * r];
        for (int i = 0; i < s.Length; i++)
            u[i * r] = s[i];
        for (int st = 0; st < n; st++)
        {
            for (int i = 1; i < u.Length; i++)
                u[i] += u[i - 1];
        }
        Assert.Equal(u, Dsp.CicInterpolate(x, r, n, m));
    }
}
