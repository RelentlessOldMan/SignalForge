using Xunit;

namespace SignalForge.Tests;

/// <summary>CIC decimator (ADR 0229).</summary>
public class CicTests
{
    [Fact]
    public void MatchesIntegratorCombStructure()
    {
        var rng = new Random(7);
        double[] x = [.. Enumerable.Range(0, 200).Select(_ => (double)rng.Next(-100, 100))];
        int r = 5, n = 4, m = 2;
        double[] s = [.. x];
        for (int st = 0; st < n; st++)
        {
            for (int i = 1; i < s.Length; i++)
                s[i] += s[i - 1];
        }
        s = [.. s.Where((_, i) => i % r == 0)];
        for (int st = 0; st < n; st++)
        {
            for (int i = s.Length - 1; i >= m; i--)
                s[i] -= s[i - m];
        }
        Assert.Equal(s, Dsp.CicDecimate(x, r, n, m));
    }

    [Fact]
    public void TapsSumToTheGain() => Assert.Equal(Math.Pow(12, 4), Dsp.CicTaps(4, 4, 3).Sum());
}
