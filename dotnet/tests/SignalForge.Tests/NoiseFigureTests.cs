using Xunit;

namespace SignalForge.Tests;

/// <summary>Noise figure by the Y-factor method (conventions: Noise figure; ADR 0105).</summary>
public class NoiseFigureTests
{
    private const double K = 1.380649e-23; // any gain-bandwidth factor cancels in Y

    public static TheoryData<double, double, double> Devices()
    {
        var d = new TheoryData<double, double, double>();
        foreach (double te in new[] { 0.0, 35, 290, 1500, 12000 })
            foreach (double tc in new[] { 77.0, 290, 300 })
                foreach (double enr in new[] { 5.0, 15, 25 })
                    d.Add(te, tc, enr);
        return d;
    }

    [Theory]
    [MemberData(nameof(Devices))]
    public void MeasuresASimulatedDevice(double te, double tc, double enrDb)
    {
        double th = 290 * (1 + Math.Pow(10, enrDb / 10));
        const double gainBw = 1e9;
        NoiseFigure r = Measurements.NoiseFigureYFactor(K * gainBw * (th + te), K * gainBw * (tc + te), enrDb, tc);
        Assert.True(Math.Abs(r.NoiseTemperature - te) <= 1e-9 * th, $"{r.NoiseTemperature} vs {te}");
        Assert.True(Math.Abs(r.NoiseFactor - (1 + te / 290)) <= 1e-12 * (1 + te / 290));
        Assert.True(Math.Abs(r.YFactor - (th + te) / (tc + te)) <= 1e-14 * r.YFactor);
    }

    [Fact]
    public void TextbookAndReducedForm()
    {
        Assert.Equal(5.4576, Measurements.NoiseFigureYFactor(10, 1, 15).NoiseFigureDb, 4); // 15 − 10·log10 9
        foreach (double y in new[] { 1.5, 4, 30 })
        {
            double want = Math.Pow(10, 1.2) / (y - 1);
            Assert.True(Math.Abs(Measurements.NoiseFigureYFactor(y, 1, 12).NoiseFactor - want) <= 1e-14 * want);
        }
        Assert.True(Measurements.NoiseFigureYFactor(12, 1, 10).NoiseFigureDb < 0);
    }

    [Theory]
    [InlineData(1.0, 1.0, 15.0, 290.0)]
    [InlineData(0.5, 1.0, 15.0, 290.0)]
    [InlineData(1.0, 0.0, 15.0, 290.0)]
    [InlineData(double.NaN, 1.0, 15.0, 290.0)]
    [InlineData(2.0, 1.0, double.PositiveInfinity, 290.0)]
    [InlineData(2.0, 1.0, 4000.0, 290.0)]
    [InlineData(1e300, 1e-300, 15.0, 290.0)]
    [InlineData(2.0, 1.0, 15.0, 0.0)]
    [InlineData(2.0, 1.0, 15.0, -10.0)]
    [InlineData(2.0, 1.0, 0.0, 580.0)]
    public void BadArguments(double hot, double cold, double enrDb, double tc) =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.NoiseFigureYFactor(hot, cold, enrDb, tc));
}
