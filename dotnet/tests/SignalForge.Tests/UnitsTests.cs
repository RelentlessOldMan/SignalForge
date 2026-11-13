namespace SignalForge.Tests;

public class UnitsTests
{
    [Theory]
    [InlineData(1e-9)]
    [InlineData(0.5)]
    [InlineData(3.7)]
    [InlineData(1e6)]
    public void RoundTrips(double x)
    {
        Assert.Equal(x, Units.DbToLin(Units.LinToDb(x)), x * 1e-14);
        Assert.Equal(x, Units.DbToAmp(Units.AmpToDb(x)), x * 1e-14);
        Assert.Equal(x, Units.DbmToW(Units.WToDbm(x)), x * 1e-14);
        Assert.Equal(x, Units.DbmToVrms(Units.VrmsToDbm(x, 75), 75), x * 1e-14);
    }

    [Fact]
    public void ZeroIsMinusInfinity() => Assert.Equal(double.NegativeInfinity, Units.LinToDb(0));

    [Theory]
    [InlineData(-1.0)]
    [InlineData(double.NaN)]
    public void NegativeOrNanThrows(double x)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Units.LinToDb(x));
        Assert.Throws<ArgumentOutOfRangeException>(() => Units.AmpToDb(x));
        Assert.Throws<ArgumentOutOfRangeException>(() => Units.WToDbm(x));
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-50.0)]
    public void BadImpedanceThrows(double r)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Units.VrmsToDbm(1, r));
        Assert.Throws<ArgumentOutOfRangeException>(() => Units.DbmToVrms(0, r));
    }
}
