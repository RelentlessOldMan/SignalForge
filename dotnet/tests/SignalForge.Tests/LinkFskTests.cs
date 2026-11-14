using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>FSK in the link (conventions: QPSK link, FSK; ADR 0057).</summary>
public class LinkFskTests
{
    [Theory]
    [InlineData("fsk2", 4, 0)]
    [InlineData("fsk2", 4, 7)]
    [InlineData("fsk2", 8, 3)]
    [InlineData("fsk2", 8, 13)]
    [InlineData("fsk2", 5, 9)]
    [InlineData("fsk4", 4, 0)]
    [InlineData("fsk4", 4, 7)]
    [InlineData("fsk4", 8, 3)]
    [InlineData("fsk4", 8, 13)]
    [InlineData("fsk4", 5, 9)]
    public void NoiselessFindsTheDelay(string modulation, int sps, int delay)
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 300,
            Modulation = modulation,
            SamplesPerSymbol = sps,
            DelaySamples = delay,
        });
        Assert.Equal(delay % sps, r.TimingOffset);
        Assert.Equal(delay / sps, r.FrameStart);
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.Equal(modulation == "fsk2" ? 300 : 600, r.BitErrors.Compared);
        Assert.Null(r.FrequencyOffsetHz);
        Assert.Null(r.PhaseOffset);
        Assert.Null(r.Evm);
        Assert.Null(r.BerTheory);
    }

    [Theory]
    [InlineData("fsk2", 20.0, 1.0, 0.0)]
    [InlineData("fsk2", -35.0, -2.5, 0.0)]
    [InlineData("fsk2", 0.0, 0.0, 60.0)]
    [InlineData("fsk2", 10.0, 3.0, -60.0)]
    [InlineData("fsk4", 20.0, 1.0, 0.0)]
    [InlineData("fsk4", -35.0, -2.5, 0.0)]
    [InlineData("fsk4", 0.0, 0.0, 60.0)]
    [InlineData("fsk4", 10.0, 3.0, -60.0)]
    public void NoiselessWithOffsetsHasNoErrors(string modulation, double df, double phase, double ppm)
    {
        // tones a symbol rate apart: a few percent of it costs nothing without noise, and a clock
        // offset that shortens the stream must not move the frame out of the search
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 500,
            Modulation = modulation,
            SamplesPerSymbol = 8,
            FrequencyOffsetHz = df,
            Phase = phase,
            ClockOffsetPpm = ppm,
            DelaySamples = 6,
        });
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.InRange(r.FrameStart * 8 + r.TimingOffset, 6, 7);
    }

    [Fact]
    public void Fsk2BerNearTheory()
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 20000,
            EbN0Db = 7.0,
            Modulation = "fsk2",
            DelaySamples = 5,
            Seed = 3,
        });
        Assert.Equal(Metrics.FskBerTheory(7.0, 2), r.BerTheory);
        double expected = r.BerTheory!.Value * r.BitErrors.Compared; // about 816; 4 sd is about 14%
        Assert.InRange(r.BitErrors.Errors, 0.85 * expected, 1.15 * expected);
        // delay 5 or 6: the first sample of a symbol also continues the tone before it
        Assert.InRange(r.FrameStart * 4 + r.TimingOffset, 5, 6);
    }

    [Fact]
    public void Fsk4BerNearTheory()
    {
        QpskLinkReport r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 20000,
            EbN0Db = 6.0,
            Modulation = "fsk4",
            DelaySamples = 2,
            FrequencyOffsetHz = 8,
            Seed = 4,
        });
        Assert.Equal(Metrics.FskBerTheory(6.0, 4), r.BerTheory);
        double expected = r.BerTheory!.Value * r.BitErrors.Compared; // about 632; 4 sd is about 16%
        Assert.InRange(r.BitErrors.Errors, 0.82 * expected, 1.18 * expected);
        Assert.InRange(r.FrameStart * 4 + r.TimingOffset, 2, 3);
    }

    [Fact]
    public void JsonHasNulls()
    {
        using JsonDocument d = JsonDocument.Parse(Link.QpskLink(new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk4" }).ToJson());
        JsonElement root = d.RootElement;
        Assert.Equal(JsonValueKind.Null, root.GetProperty("frequency_offset_hz").ValueKind);
        Assert.Equal(JsonValueKind.Null, root.GetProperty("phase_offset").ValueKind);
        Assert.Equal(JsonValueKind.Null, root.GetProperty("evm").ValueKind);
        Assert.Equal("fsk4", root.GetProperty("config").GetProperty("modulation").GetString());
    }

    public static TheoryData<QpskLinkConfig> Rejected() => new()
    {
        new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk4", SamplesPerSymbol = 3 },
        new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk2", TimingLoopGains = [0.01, 0.0001] },
        new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk4", CarrierLoopGains = [0.05, 0.001] },
        new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk8" },
        new QpskLinkConfig { NumSymbols = 64, Modulation = "fsk2", Rolloff = 1.5 },
    };

    [Theory]
    [MemberData(nameof(Rejected))]
    public void Rejects(QpskLinkConfig config) =>
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(config));

    [Fact]
    public void UnknownModulationListsFsk()
    {
        var e = Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(new QpskLinkConfig { NumSymbols = 64, Modulation = "bpsk" }));
        Assert.Contains("fsk2", e.Message, StringComparison.Ordinal);
    }
}
