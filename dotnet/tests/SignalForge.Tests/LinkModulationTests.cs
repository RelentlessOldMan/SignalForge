using Xunit;

namespace SignalForge.Tests;

/// <summary>16-QAM, 8-PSK and 64-QAM in the link (conventions: QPSK link; ADR 0050, 0051, 0053).</summary>
public class LinkModulationTests
{
    [Theory]
    [InlineData(30.0, 2.6, 1)]
    [InlineData(-90.0, -0.4, 7)]
    [InlineData(0.0, 0.0, 0)]
    public void Qam16NoiselessHasNoErrors(double df, double phase, int delay)
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 400,
            Modulation = "qam16",
            FrequencyOffsetHz = df,
            Phase = phase,
            DelaySamples = delay,
        });
        Assert.Equal(1600, r.BitErrors.Compared);
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.Null(r.BerTheory);
    }

    [Fact]
    public void Qam16BerNearTheory()
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 20000,
            EbN0Db = 8,
            Modulation = "qam16",
            FrequencyOffsetHz = 15,
            Phase = -0.9,
            DelaySamples = 6,
            PreambleSymbols = 64,
            Seed = 21,
        });
        double expected = r.BerTheory!.Value * r.BitErrors.Compared; // about 740
        Assert.InRange(r.BitErrors.Errors, 0.85 * expected, 1.2 * expected);
        Assert.InRange(r.FrequencyOffsetHz, 14.95, 15.05);
    }

    [Fact]
    public void Qam16CarrierLoop()
    {
        var (kp, ki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 1.0); // 16-QAM detector slope about 1
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 2000,
            EbN0Db = 14,
            Modulation = "qam16",
            FrequencyOffsetHz = -12,
            Phase = 1.0,
            CarrierLoopGains = [kp, ki],
            Seed = 2,
        });
        Assert.True(r.BitErrors.Errors <= 3, $"errors {r.BitErrors.Errors}");
    }

    [Fact]
    public void DefaultIsQpsk()
    {
        var cfg = new QpskLinkConfig { NumSymbols = 300, EbN0Db = 6, FrequencyOffsetHz = 5, Seed = 1 };
        Assert.Equal(Link.QpskLink(cfg).ToJson(), Link.QpskLink(cfg with { Modulation = "qpsk" }).ToJson());
        Assert.Equal(600, Link.QpskLink(cfg).BitErrors.Compared);
    }

    [Fact]
    public void BadModulationThrows()
    {
        var c = new QpskLinkConfig { NumSymbols = 50 };
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { Modulation = "8psk" }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { Modulation = null! }));
    }

    [Theory]
    [InlineData(41.0, -2.2, 5)]
    [InlineData(-55.0, 0.7, 2)]
    [InlineData(0.0, 0.0, 0)]
    public void Psk8NoiselessHasNoErrors(double df, double phase, int delay)
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 400,
            Modulation = "psk8",
            FrequencyOffsetHz = df,
            Phase = phase,
            DelaySamples = delay,
        });
        Assert.Equal(1200, r.BitErrors.Compared);
        Assert.Equal(0, r.BitErrors.Errors);
    }

    [Fact]
    public void Psk8BerNearTheory()
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 20000,
            EbN0Db = 10,
            Modulation = "psk8",
            FrequencyOffsetHz = -22,
            Phase = 0.6,
            DelaySamples = 3,
            PreambleSymbols = 64,
            Seed = 8,
        });
        double expected = r.BerTheory!.Value * r.BitErrors.Compared; // about 61
        Assert.InRange(r.BitErrors.Errors, 0.6 * expected, 1.5 * expected);
        Assert.InRange(r.FrequencyOffsetHz, -22.05, -21.95);
    }

    [Fact]
    public void Psk8CarrierLoop()
    {
        var (kp, ki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 1.0);
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 2000,
            EbN0Db = 14,
            Modulation = "psk8",
            FrequencyOffsetHz = -12,
            Phase = 1.0,
            CarrierLoopGains = [kp, ki],
            Seed = 2,
        });
        Assert.True(r.BitErrors.Errors <= 3, $"errors {r.BitErrors.Errors}");
    }

    [Theory]
    [InlineData(-20.0, 0.4, 2)]
    [InlineData(60.0, -2.9, 6)]
    public void Qam64NoiselessHasNoErrors(double df, double phase, int delay)
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 400,
            Modulation = "qam64",
            FrequencyOffsetHz = df,
            Phase = phase,
            DelaySamples = delay,
        });
        Assert.Equal(2400, r.BitErrors.Compared);
        Assert.Equal(0, r.BitErrors.Errors);
    }

    [Fact]
    public void Qam64BerNearTheory()
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 20000,
            EbN0Db = 14,
            Modulation = "qam64",
            FrequencyOffsetHz = 9,
            Phase = 1.7,
            DelaySamples = 4,
            PreambleSymbols = 64,
            PhaseBlockSymbols = 128,
            Seed = 33,
        });
        double expected = r.BerTheory!.Value * r.BitErrors.Compared; // about 258
        Assert.InRange(r.BitErrors.Errors, 0.85 * expected, 1.25 * expected);
        Assert.InRange(r.FrequencyOffsetHz, 8.95, 9.05);
    }

    [Fact]
    public void Qam64CarrierLoop()
    {
        var (kp, ki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 1.0); // mean detector slope 1
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 2000,
            EbN0Db = 18,
            Modulation = "qam64",
            FrequencyOffsetHz = -12,
            Phase = 1.0,
            PhaseBlockSymbols = 128,
            CarrierLoopGains = [kp, ki],
            Seed = 2,
        });
        Assert.True(r.BitErrors.Errors <= 3, $"errors {r.BitErrors.Errors}");
    }
}
