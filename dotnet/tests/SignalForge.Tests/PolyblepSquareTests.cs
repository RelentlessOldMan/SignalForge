using Xunit;

namespace SignalForge.Tests;

/// <summary>PolyBLEP square (ADR 0311).</summary>
public class PolyblepSquareTests
{
    [Fact]
    public void OnlyTheSamplesNextToAnEdgeChange()
    {
        double[] naive = Waveforms.Square(8000, 16, 1000, 0.5, 1, 0.0625);
        double[] y = Waveforms.PolyblepSquare(8000, 16, 1000, 0.5, 1, 0.0625);
        for (int n = 0; n < y.Length; n++)
        {
            if (n % 4 is 0 or 3)
                Assert.NotEqual(naive[n], y[n]);
            else
                Assert.Equal(naive[n], y[n]);
        }
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(1.0)]
    public void ADutyOfZeroOrOneIsTheNaiveConstant(double duty)
    {
        double[] y = Waveforms.PolyblepSquare(8000, 16, 1000, duty, 1, 0.0625);
        Assert.All(y, v => Assert.Equal(duty == 0 ? -1.0 : 1.0, v));
    }

    [Theory]
    [InlineData(-0.1)]
    [InlineData(1.1)]
    public void RejectsADutyOutsideZeroToOne(double duty) =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepSquare(8000, 4, 1000, duty));

    [Fact]
    public void RejectsAFrequencyAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepSquare(8000, 4, 4001));
}
