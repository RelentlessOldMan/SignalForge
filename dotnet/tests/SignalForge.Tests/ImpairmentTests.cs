using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>IQ imbalance and DC offset: the image a tone gets, the Q branch's phase, and the
/// offset's mean (conventions: Channel, IQ imbalance, Image rejection, DC offset).</summary>
public class ImpairmentTests
{
    private static Complex Bin(Complex[] x, int k)
    {
        Complex sum = 0;
        for (int n = 0; n < x.Length; n++)
            sum += x[n] * Complex.FromPolarCoordinates(1, -2 * Math.PI * k * n / x.Length);
        return sum;
    }

    [Theory]
    [InlineData(0.5, 0.0)]
    [InlineData(0.0, 0.03)]
    [InlineData(-1.0, -0.2)]
    [InlineData(2.0, 1.0)]
    [InlineData(0.1, Math.PI / 180)]
    public void AToneImageMatchesTheImageRejection(double gainDb, double phase)
    {
        const int n = 64, k = 5;
        Complex[] x = [.. Enumerable.Range(0, n).Select(i => Complex.FromPolarCoordinates(1, 2 * Math.PI * k * i / n))];
        Complex[] y = Channel.IqImbalance(x, gainDb, phase);
        double measured = 10 * Math.Log10(Math.Pow(Bin(y, k).Magnitude, 2) / Math.Pow(Bin(y, n - k).Magnitude, 2));
        Assert.Equal(Channel.IqImageRejectionDb(gainDb, phase), measured, 1e-9);
        for (int b = 0; b < n; b++)
            if (b != k && b != n - k)
                Assert.True(Bin(y, b).Magnitude < 1e-12 * n, $"bin {b}");
    }

    [Fact]
    public void TheQBranchIsAdvancedAndScaled()
    {
        double g = Math.Pow(10, 1.5 / 20), phase = 0.3;
        for (int i = 0; i <= 36; i++)
        {
            double theta = 2 * Math.PI * i / 36;
            Complex y = Channel.IqImbalance([Complex.FromPolarCoordinates(1, theta)], 1.5, phase)[0];
            Assert.Equal(Math.Cos(theta), y.Real, 1e-15);
            Assert.Equal(g * Math.Sin(theta + phase), y.Imaginary, 1e-14);
        }
    }

    [Fact]
    public void NoImbalanceIsTheIdentityAndHasNoImage()
    {
        Complex[] x = [new(0.3, -1.2), 2, new(0, -1)];
        Assert.Equal(x, Channel.IqImbalance(x, 0, 0));
        Assert.Equal(double.PositiveInfinity, Channel.IqImageRejectionDb(0, 0));
    }

    [Fact]
    public void ImageRejectionDoesNotDependOnTheSignOfTheGainError()
    {
        foreach (double phase in new[] { 0.0, 0.1, -0.4 })
            Assert.Equal(Channel.IqImageRejectionDb(-1.2, phase), Channel.IqImageRejectionDb(1.2, phase), 1e-12);
    }

    [Fact]
    public void DcOffsetMovesTheMean()
    {
        Complex[] x = [.. Enumerable.Range(0, 16).Select(i => Complex.FromPolarCoordinates(1, 2 * Math.PI * i / 16))];
        Complex[] y = Channel.DcOffset(x, new Complex(0.25, -0.5));
        Complex mean = y.Aggregate(Complex.Zero, (s, v) => s + v) / y.Length;
        Assert.True(Complex.Abs(mean - new Complex(0.25, -0.5)) < 1e-15, $"{mean}");
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Channel.IqImbalance([Complex.ImaginaryOne], double.NaN, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.IqImbalance([Complex.ImaginaryOne], 0, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Channel.IqImbalance([Complex.ImaginaryOne], 7000, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.IqImageRejectionDb(0, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Channel.DcOffset([Complex.ImaginaryOne], new Complex(double.PositiveInfinity, 0)));
    }
}
