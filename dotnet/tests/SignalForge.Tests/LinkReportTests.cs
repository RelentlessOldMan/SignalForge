using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The end-to-end QPSK link and its JSON report.</summary>
public class LinkReportTests
{
    // The JSON field names; the Python tests check the same list.
    private static readonly string[] ReportKeys =
        ["config", "timing_offset", "frame_start", "frequency_offset_hz", "phase_offset", "evm", "bit_errors", "ber_theory"];

    private static readonly string[] ConfigKeys =
    [
        "num_symbols", "eb_n0_db", "symbol_rate", "samples_per_symbol", "rolloff", "span_symbols", "delay_samples",
        "frequency_offset_hz", "phase", "preamble_symbols", "phase_block_symbols", "prbs_order", "seed", "phase_noise_linewidth_hz",
        "clock_offset_ppm",
        "timing_loop_gains", "carrier_loop_gains",
    ];

    private static string[] Keys(JsonElement e) => e.EnumerateObject().Select(p => p.Name).ToArray();

    [Theory]
    [InlineData(0.0, 1.0, 2)]
    [InlineData(20.0, -2.5, 3)]
    [InlineData(-60.0, 0.4, 0)]
    public void BerMatchesTheoryAt6Db(double df, double phase, int delay)
    {
        var r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 100_000,
            EbN0Db = 6,
            DelaySamples = delay,
            FrequencyOffsetHz = df,
            Phase = phase,
            Seed = 3,
        });
        Assert.NotNull(r.BerTheory);
        // theory 2.39e-3 over 200k bits is about 480 errors; offsets before the matched filter add a
        // little interference, so allow 20%
        Assert.True(Math.Abs(r.BitErrors.Rate / r.BerTheory.Value - 1) < 0.2, $"ber {r.BitErrors.Rate}");
        Assert.True(Math.Abs(r.FrequencyOffsetHz - df) < 0.01, $"f {r.FrequencyOffsetHz}");
        Assert.Equal(100_000, r.Evm.NumSymbols);
    }

    [Fact]
    public void JsonReportShape()
    {
        using var d = JsonDocument.Parse(Link.QpskLink(new QpskLinkConfig { NumSymbols = 64, EbN0Db = 8 }).ToJson());
        var root = d.RootElement;
        Assert.Equal(ReportKeys, Keys(root));
        Assert.Equal(ConfigKeys, Keys(root.GetProperty("config")));
        Assert.Equal(["rms", "rms_percent", "rms_db", "peak", "peak_index", "num_symbols"], Keys(root.GetProperty("evm")));
        Assert.Equal(["errors", "compared", "rate"], Keys(root.GetProperty("bit_errors")));
        Assert.Equal(8.0, root.GetProperty("config").GetProperty("eb_n0_db").GetDouble());
        Assert.True(root.GetProperty("frame_start").TryGetInt32(out _));
        Assert.Equal(128, root.GetProperty("bit_errors").GetProperty("compared").GetInt32());
    }

    [Fact]
    public void NoiselessReportHasNullTheory()
    {
        using var d = JsonDocument.Parse(Link.QpskLink(new QpskLinkConfig { NumSymbols = 50 }).ToJson());
        Assert.Equal(JsonValueKind.Null, d.RootElement.GetProperty("ber_theory").ValueKind);
        Assert.Equal(JsonValueKind.Null, d.RootElement.GetProperty("config").GetProperty("eb_n0_db").ValueKind);
    }

    [Fact]
    public void NonFiniteNumbersAreStrings()
    {
        var evm = new Evm(0, 0, double.NegativeInfinity, 0, 0, 2);
        var r = new QpskLinkReport(new QpskLinkConfig { NumSymbols = 2 }, double.NaN, 0, double.PositiveInfinity, 0, evm,
            new ErrorCount(0, 0, double.NaN), null);
        using var d = JsonDocument.Parse(r.ToJson());
        Assert.Equal("nan", d.RootElement.GetProperty("timing_offset").GetString());
        Assert.Equal("inf", d.RootElement.GetProperty("frequency_offset_hz").GetString());
        Assert.Equal("-inf", d.RootElement.GetProperty("evm").GetProperty("rms_db").GetString());
        Assert.Equal("nan", d.RootElement.GetProperty("bit_errors").GetProperty("rate").GetString());
    }

    [Fact]
    public void Rejects()
    {
        var ok = new QpskLinkConfig { NumSymbols = 50 };
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(ok with { Seed = -1 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(ok with { Phase = double.PositiveInfinity }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(ok with { PrbsOrder = 8 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(ok with { Rolloff = 1.5 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(null!));
    }
}
