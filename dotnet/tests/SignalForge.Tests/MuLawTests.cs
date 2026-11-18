using Xunit;

namespace SignalForge.Tests;

/// <summary>μ-law companding (ADR 0248).</summary>
public class MuLawTests
{
    [Fact]
    public void AnchorsAreExact()
    {
        double[] y = Dsp.MuLawCompress([1 / 255.0, 15 / 255.0, -1.0]);
        Assert.Equal(0.125, y[0], 1e-16);
        Assert.Equal(0.5, y[1], 1e-16);
        Assert.Equal(-1.0, y[2], 1e-16);
    }

    [Fact]
    public void RoundTrips()
    {
        double[] x = [.. Enumerable.Range(-100, 201).Select(i => i / 100.0)];
        double[] back = Dsp.MuLawExpand(Dsp.MuLawCompress(x));
        for (int i = 0; i < x.Length; i++)
            Assert.Equal(x[i], back[i], 1e-15);
    }
}
