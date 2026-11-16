using Xunit;

namespace SignalForge.Tests;

/// <summary>Cascaded noise figure by Friis' formula (conventions: Noise figure, Cascade;
/// ADR 0106).</summary>
public class NoiseFigureCascadeTests
{
    [Fact]
    public void NoiseTemperaturesAddThroughTheGain()
    {
        double[] te = [50, 400, 2000];
        double[] g = [15, 8, -3];
        double[] nf = [.. te.Select(t => 10 * Math.Log10(1 + t / 290))];
        CascadeNoiseFigure r = Measurements.NoiseFigureCascade(nf, g);
        double want = te[0] + te[1] / Math.Pow(10, 1.5) + te[2] / Math.Pow(10, 2.3);
        Assert.True(Math.Abs(r.NoiseTemperature - want) <= 1e-12 * want, $"{r.NoiseTemperature} vs {want}");
        Assert.Equal(20, r.GainDb, 12);
        Assert.Equal(r.NoiseFactor, r.Contributions.Sum(), 12);
    }

    [Theory]
    [InlineData(3.0, 1.5)]
    [InlineData(6.0, 2.0)]
    [InlineData(10.0, 0.5)]
    public void LossInFrontAddsInDb(double loss, double nf2) =>
        Assert.Equal(loss + nf2, Measurements.NoiseFigureCascade([loss, nf2], [-loss, 25]).NoiseFigureDb, 12);

    [Fact]
    public void OneStageIsItselfAndAHugeFirstGainHidesTheRest()
    {
        CascadeNoiseFigure one = Measurements.NoiseFigureCascade([4.5], [12]);
        Assert.Equal(4.5, one.NoiseFigureDb, 12);
        Assert.Single(one.Contributions);
        Assert.Equal(2, Measurements.NoiseFigureCascade([2, 30, 30], [300, 300, 0]).NoiseFigureDb, 12);
        Assert.Equal(1, Measurements.NoiseFigureCascade([1, 1], [4000, 0]).NoiseFigureDb, 12);
    }

    public static TheoryData<double[], double[]> Bad() => new()
    {
        { [], [] },
        { [1.0], [1.0, 2.0] },
        { [1.0, -0.5], [1.0, 1.0] },
        { [double.NaN], [1.0] },
        { [1.0], [double.NegativeInfinity] },
        { [1.0, 2.0], [-4000.0, 0.0] },
        { [4000.0], [0.0] },
    };

    [Theory]
    [MemberData(nameof(Bad))]
    public void BadArguments(double[] nf, double[] g) =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.NoiseFigureCascade(nf, g));
}
