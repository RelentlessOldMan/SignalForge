using Xunit;

namespace SignalForge.Tests;

/// <summary>PolyBLEP triangle (ADR 0314).</summary>
public class PolyblepTriangleTests
{
    [Fact]
    public void OnlyTheCornerSamplesChangeAtEightSamplesACycle()
    {
        double[] naive = Waveforms.Triangle(8000, 16, 1000);
        double[] y = Waveforms.PolyblepTriangle(8000, 16, 1000);
        for (int n = 0; n < y.Length; n++)
        {
            double expected = n % 4 == 0 ? naive[n] - (Math.Sign(naive[n]) / 6.0) : naive[n];
            Assert.Equal(expected, y[n], 1e-15);
        }
    }

    [Fact]
    public void RejectsAFrequencyAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepTriangle(8000, 4, -4001));
}
