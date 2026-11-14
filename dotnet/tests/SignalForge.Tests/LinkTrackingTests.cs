using Xunit;

namespace SignalForge.Tests;

/// <summary>Clock offset and tracking loops in the QPSK link (conventions: QPSK link; ADR 0046).</summary>
public class LinkTrackingTests
{
    // gains for a loop bandwidth of 0.01 per symbol: the Gardner detector's slope on this pulse is
    // about 0.26 (measured open loop, TimingLoopTests), the carrier detector's √2 at unit amplitude
    private static readonly (double Kp, double Ki) Timing = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 0.26);
    private static readonly (double Kp, double Ki) Carrier = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), Math.Sqrt(2));

    private static readonly QpskLinkConfig Drifting = new()
    {
        NumSymbols = 3000,
        EbN0Db = 6,
        ClockOffsetPpm = 400, // 4.8 samples of drift over the frame, more than a symbol
        FrequencyOffsetHz = 7,
        Phase = 0.3,
        DelaySamples = 1,
        Seed = 3,
    };

    [Fact]
    public void TimingLoopFollowsAClockOffset()
    {
        Assert.True(Link.QpskLink(Drifting).BitErrors.Rate > 0.1);
        foreach (var cfg in new[]
        {
            Drifting with { TimingLoopGains = [Timing.Kp, Timing.Ki] },
            Drifting with { TimingLoopGains = [Timing.Kp, Timing.Ki], CarrierLoopGains = [Carrier.Kp, Carrier.Ki] },
        })
        {
            QpskLinkReport r = Link.QpskLink(cfg);
            // theory is about 14 errors in 6000 bits; 5 sd of a Poisson count is about 19
            Assert.True(r.BitErrors.Errors < 14 + 19, $"{r.BitErrors.Errors} errors");
            Assert.True(r.Evm!.Rms < 0.4);
        }
    }

    [Fact]
    public void LoopsWithoutAnOffsetChangeLittle()
    {
        var cfg = new QpskLinkConfig { NumSymbols = 2000, EbN0Db = 8, FrequencyOffsetHz = -15, Seed = 5 };
        QpskLinkReport plain = Link.QpskLink(cfg);
        QpskLinkReport looped = Link.QpskLink(cfg with { TimingLoopGains = [Timing.Kp, Timing.Ki], CarrierLoopGains = [Carrier.Kp, Carrier.Ki] });
        Assert.True(Math.Abs(looped.Evm!.Rms - plain.Evm!.Rms) < 0.02);
        Assert.True(Math.Abs(looped.BitErrors.Errors - plain.BitErrors.Errors) <= 10);
    }

    [Fact]
    public void CarrierLoopFollowsPhaseNoise()
    {
        // 0.15 Hz at 1000 Bd is 0.03 rad rms per symbol, wandering about 1.7 rad over 3000
        // symbols, which one line through the block phases cannot follow; the loop at Bn 0.03 can
        var gains = Sync.PiLoopGains(0.03, 1 / Math.Sqrt(2), Math.Sqrt(2));
        int block = 0, looped = 0;
        for (int seed = 0; seed < 5; seed++)
        {
            var cfg = new QpskLinkConfig { NumSymbols = 3000, EbN0Db = 8, PhaseNoiseLinewidthHz = 0.15, FrequencyOffsetHz = 5, Seed = seed };
            block += Link.QpskLink(cfg).BitErrors.Errors;
            looped += Link.QpskLink(cfg with { CarrierLoopGains = [gains.Kp, gains.Ki] }).BitErrors.Errors;
        }
        // theory 1.9e-4 is about 6 errors in 30000 bits; a cycle slip would cost hundreds
        Assert.True(block > 300, $"block {block}");
        Assert.True(looped < 40, $"looped {looped}");
    }

    [Fact]
    public void NoPhaseNoiseDrawsNothing()
    {
        var cfg = new QpskLinkConfig { NumSymbols = 500, EbN0Db = 5, Seed = 9 };
        Assert.Equal(Link.QpskLink(cfg).ToJson(), Link.QpskLink(cfg with { PhaseNoiseLinewidthHz = 0 }).ToJson());
    }

    [Fact]
    public void GainsSerializeAsPairs()
    {
        string json = Link.QpskLink(new QpskLinkConfig { NumSymbols = 64, TimingLoopGains = [0.1, 0.001] }).ToJson();
        using var doc = System.Text.Json.JsonDocument.Parse(json);
        var c = doc.RootElement.GetProperty("config");
        Assert.Equal([0.1, 0.001], c.GetProperty("timing_loop_gains").EnumerateArray().Select(e => e.GetDouble()));
        Assert.Equal(System.Text.Json.JsonValueKind.Null, c.GetProperty("carrier_loop_gains").ValueKind);
        Assert.Equal(0.0, c.GetProperty("clock_offset_ppm").GetDouble());
    }

    [Fact]
    public void BadSettingsThrow()
    {
        var c = new QpskLinkConfig { NumSymbols = 50 };
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { ClockOffsetPpm = 2e5 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { PhaseNoiseLinewidthHz = -1 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { PhaseNoiseLinewidthHz = double.PositiveInfinity }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { ClockOffsetPpm = double.NaN }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { TimingLoopGains = [0.1] }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { TimingLoopGains = [0.1, -0.01] }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { CarrierLoopGains = [0.1, double.NaN] }));
    }
}
