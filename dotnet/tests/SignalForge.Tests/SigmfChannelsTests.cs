using System.Numerics;
using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Multi-channel SigMF recordings (conventions: Signal files, Channels; ADR 0096).</summary>
public sealed class SigmfChannelsTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string P(string name) => Path.Combine(_dir, name);

    private static Dictionary<string, object?> Burst() => new()
    {
        ["core:sample_start"] = 1L,
        ["core:sample_count"] = 2L,
        ["core:label"] = "burst",
    };

    private static Signal<T> Channel<T>(T[] samples, double frequency = 2.4e9, double timeOrigin = 0.5,
        string units = "V", double impedance = 50, Dictionary<string, object?>? metadata = null) where T : struct =>
        new(samples, 2e6, frequency, timeOrigin, units, impedance,
            metadata ?? new Dictionary<string, object?>
            {
                ["core:annotations"] = new List<object?> { Burst() },
                ["run"] = 3L,
                ["x:gain"] = 1.5,
            });

    private void WriteMeta(string name, string datatype, long channels, byte[] data)
    {
        File.WriteAllText(P(name + ".sigmf-meta"),
            $$$"""{"global": {"core:datatype": "{{{datatype}}}", "core:version": "1.0.0", "core:sample_rate": 1, "core:num_channels": {{{channels}}}}}""");
        File.WriteAllBytes(P(name + ".sigmf-data"), data);
    }

    [Fact]
    public void RoundTrip()
    {
        Signal<Complex>[] chans =
        [
            Channel<Complex>([new(1, 2), new(0, -0.5), 0.25]),
            Channel<Complex>([3, new(0, 4), new(-1, -1)]),
        ];
        SignalFiles.WriteSigmfChannels(P("r"), chans);
        var back = SignalFiles.ReadSigmfChannels<Complex>(P("r"));
        Assert.Equal(2, back.Count);
        for (int c = 0; c < 2; c++)
        {
            Assert.Equal(chans[c].Samples.ToArray(), back[c].Samples.ToArray());
            Assert.Equal((2e6, 2.4e9, 0.5, "V", (double?)50.0),
                (back[c].SampleRate, back[c].CenterFrequency, back[c].TimeOrigin, back[c].Units, back[c].Impedance));
            Assert.Equal(3L, back[c].Metadata["run"]);
            Assert.Equal(1.5, back[c].Metadata["x:gain"]);
            var spans = (List<object?>)back[c].Metadata["core:annotations"]!;
            Assert.Equal(Burst(), (Dictionary<string, object?>)spans[0]!);
        }
    }

    [Fact]
    public void SamplesAreInterleavedFrameByFrame()
    {
        SignalFiles.WriteSigmfChannels(P("i"), [new Signal<double>([1, 2], 10), new Signal<double>([3, 4], 10)]);
        Assert.Equal(SignalFiles.EncodeSamples([1.0, 3, 2, 4], "rf64_le"), File.ReadAllBytes(P("i.sigmf-data")));
        using var doc = JsonDocument.Parse(File.ReadAllText(P("i.sigmf-meta")));
        var keys = doc.RootElement.GetProperty("global").EnumerateObject().Select(p => p.Name).ToList();
        Assert.Equal(keys.IndexOf("core:sample_rate") + 1, keys.IndexOf("core:num_channels"));
        Assert.Equal(2, doc.RootElement.GetProperty("global").GetProperty("core:num_channels").GetInt32());
    }

    [Fact]
    public void ReadingTakesEveryNthSample()
    {
        WriteMeta("t", "ri16_le", 3, SignalFiles.EncodeSamples([1 / 32768.0, 2 / 32768.0, 3 / 32768.0, 4 / 32768.0, 5 / 32768.0, 6 / 32768.0], "ri16_le"));
        var got = SignalFiles.ReadSigmfChannels<double>(P("t")).Select(s => s.Samples.ToArray().Select(v => v * 32768).ToArray()).ToArray();
        Assert.Equal([[1.0, 4], [2.0, 5], [3.0, 6]], got);
    }

    [Fact]
    public void OneChannelWritesTheWriteSigmfFiles()
    {
        var s = Channel<Complex>([new(0.5, 1), -0.25]);
        SignalFiles.WriteSigmf(P("a"), s, "cf32_le");
        SignalFiles.WriteSigmfChannels(P("b"), [s], "cf32_le");
        foreach (string ext in (string[])[".sigmf-meta", ".sigmf-data"])
            Assert.Equal(File.ReadAllBytes(P("a" + ext)), File.ReadAllBytes(P("b" + ext)));
        Assert.DoesNotContain("core:num_channels", File.ReadAllText(P("b.sigmf-meta")), StringComparison.Ordinal);
        Assert.Equal(SignalFiles.ReadSigmf<Complex>(P("a")).Samples.ToArray(),
            Assert.Single(SignalFiles.ReadSigmfChannels<Complex>(P("a"))).Samples.ToArray());
    }

    [Fact]
    public void ReadSigmfRefusesSeveralChannels()
    {
        SignalFiles.WriteSigmfChannels(P("two"), [new Signal<double>([1.0], 1), new Signal<double>([2.0], 1)]);
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadSigmf<double>(P("two")));
        Assert.Contains("ReadSigmfChannels", e.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void EachChannelHasItsOwnMetadata()
    {
        SignalFiles.WriteSigmfChannels(P("m"), [Channel<double>([1.0]), Channel<double>([2.0])]);
        var both = SignalFiles.ReadSigmfChannels<double>(P("m"));
        var a = (List<object?>)both[0].Metadata["core:annotations"]!;
        var b = (List<object?>)both[1].Metadata["core:annotations"]!;
        Assert.NotSame(a, b);
        ((Dictionary<string, object?>)a[0]!)["core:label"] = "changed";
        Assert.Equal("burst", ((Dictionary<string, object?>)b[0]!)["core:label"]);
    }

    [Fact]
    public void TheMostChannelsAreRead()
    {
        WriteMeta("w", "ri8", SignalFiles.MaxChannels, []);
        Assert.Equal(SignalFiles.MaxChannels, SignalFiles.ReadSigmfChannels<double>(P("w")).Count);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    [InlineData(SignalFiles.MaxChannels + 1)]
    public void BadChannelCountsAreRejected(long channels)
    {
        WriteMeta("n", "ri8", channels, []);
        Assert.Throws<ArgumentException>(() => SignalFiles.ReadSigmfChannels<double>(P("n")));
    }

    [Fact]
    public void APartialFrameIsRejected()
    {
        WriteMeta("p", "ri8", 2, [1, 2, 3]);
        Assert.Throws<ArgumentException>(() => SignalFiles.ReadSigmfChannels<double>(P("p")));
    }

    public static TheoryData<Signal<double>[]> BadLists => new()
    {
        Array.Empty<Signal<double>>(),
        new[] { Channel<double>([1.0]), Channel<double>([1.0, 2.0]) },
        new[] { Channel<double>([1.0]), new Signal<double>([1.0], 2e6) },
        new[] { Channel<double>([1.0]), Channel<double>([1.0], units: "A") },
        new[] { Channel<double>([1.0]), Channel<double>([1.0], impedance: 75) },
        new[] { Channel<double>([1.0]), Channel<double>([1.0], timeOrigin: 0) },
        new[] { Channel<double>([1.0]), Channel<double>([1.0], frequency: 0) },
        new[]
        {
            Channel<double>([1.0], metadata: new() { ["run"] = 1L }),
            Channel<double>([1.0], metadata: new() { ["run"] = 1.0 }),
        },
        new[]
        {
            Channel<double>([1.0], metadata: new() { ["run"] = 1L }),
            Channel<double>([1.0], metadata: new() { ["run"] = 1L, ["x:y"] = 2L }),
        },
    };

    [Theory]
    [MemberData(nameof(BadLists))]
    public void BadChannelListsAreRejected(Signal<double>[] channels)
    {
        SignalFiles.WriteSigmf(P("keep"), new Signal<double>([0.5], 1));
        byte[] before = File.ReadAllBytes(P("keep.sigmf-meta"));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmfChannels(P("keep"), channels));
        Assert.Equal(before, File.ReadAllBytes(P("keep.sigmf-meta")));
    }

    [Fact]
    public void ANullChannelIsRejected() =>
        Assert.Throws<ArgumentNullException>(() => SignalFiles.WriteSigmfChannels(P("z"), [new Signal<double>([1.0], 1), null!]));

    [Fact]
    public void TooManyChannelsAreRejected()
    {
        var one = new Signal<double>([], 1);
        var e = Assert.Throws<ArgumentException>(() =>
            SignalFiles.WriteSigmfChannels(P("x"), Enumerable.Repeat(one, SignalFiles.MaxChannels + 1).ToArray()));
        Assert.Contains("65535", e.Message, StringComparison.Ordinal);
        Assert.False(File.Exists(P("x.sigmf-meta")));
    }
}
