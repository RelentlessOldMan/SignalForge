using Xunit;

namespace SignalForge.Tests;

/// <summary>A-law companding (ADR 0249).</summary>
public class ALawTests
{
    [Fact]
    public void AEqualsOneIsTheIdentity()
    {
        double[] x = [0.5, -0.25, 1.0];
        Assert.Equal(x, Dsp.ALawCompress(x, 1.0));
    }

    [Fact]
    public void RoundTrips()
    {
        double[] x = [.. Enumerable.Range(-100, 201).Select(i => i / 100.0)];
        double[] back = Dsp.ALawExpand(Dsp.ALawCompress(x));
        for (int i = 0; i < x.Length; i++)
            Assert.Equal(x[i], back[i], 1e-15);
    }
}
