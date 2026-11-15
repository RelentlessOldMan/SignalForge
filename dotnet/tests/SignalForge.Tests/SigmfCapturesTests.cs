using Xunit;

namespace SignalForge.Tests;

/// <summary>Reading multi-capture SigMF recordings (conventions: Signal files, Captures; ADR 0097).</summary>
public sealed class SigmfCapturesTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    /// <summary>Writes six ri16 samples with codes 1 to 6 at 8 Hz, with the given JSON pieces.</summary>
    private string Write(string name, string captures, string annotations = "[]", string glob = "")
    {
        string path = Path.Combine(_dir, name);
        File.WriteAllText(path + ".sigmf-meta",
            "{\"global\": {\"core:datatype\": \"ri16_le\", \"core:version\": \"1.0.0\", \"core:sample_rate\": 8" + glob +
            "}, \"captures\": " + captures + ", \"annotations\": " + annotations + "}");
        File.WriteAllBytes(path + ".sigmf-data", [1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0]);
        return path;
    }

    private static double[] Codes(Signal<double> s) => [.. s.Samples.ToArray().Select(v => v * 32768)];

    private static List<Dictionary<string, object?>> Spans(Signal<double> s) =>
        [.. ((List<object?>)s.Metadata["core:annotations"]!).Cast<Dictionary<string, object?>>()];

    [Fact]
    public void SegmentsSplitAtEachStart()
    {
        var segs = SignalFiles.ReadSigmfCaptures<double>(Write("s",
            """[{"core:sample_start": 0, "core:frequency": 1e6}, {"core:sample_start": 1}, {"core:sample_start": 4, "core:frequency": -5.5}]""",
            glob: ", \"signalforge:time_origin\": 2"));
        Assert.Equal([[1.0], [2.0, 3, 4], [5.0, 6]], segs.Select(Codes).ToArray());
        Assert.Equal([1e6, 0.0, -5.5], segs.Select(s => s.CenterFrequency));
        Assert.Equal([2.0, 2 + 1 / 8.0, 2 + 4 / 8.0], segs.Select(s => s.TimeOrigin));
        Assert.All(segs, s => Assert.Equal(8, s.SampleRate));
    }

    [Fact]
    public void AnnotationsAreRebasedIntoTheirSegment()
    {
        var segs = SignalFiles.ReadSigmfCaptures<double>(Write("a",
            """[{"core:sample_start": 0}, {"core:sample_start": 3}]""",
            """[{"core:sample_start": 2, "core:sample_count": 4}, {"core:sample_start": 3, "core:label": "edge"}, {"core:sample_start": 9}]"""));
        var first = Assert.Single(Spans(segs[0]));
        Assert.Equal((2L, 4L), (first["core:sample_start"], first["core:sample_count"]));
        var second = Spans(segs[1]);
        Assert.Equal([0L, 6L], second.Select(x => x["core:sample_start"]));
        Assert.Equal("edge", second[0]["core:label"]);
        Assert.Equal(["core:sample_start", "core:label"], second[0].Keys);
    }

    [Fact]
    public void ASegmentWithoutAnnotationsHasNoKey()
    {
        var segs = SignalFiles.ReadSigmfCaptures<double>(Write("k",
            """[{"core:sample_start": 0}, {"core:sample_start": 3}]""", """[{"core:sample_start": 4}]"""));
        Assert.False(segs[0].Metadata.ContainsKey("core:annotations"));
        Assert.Equal(1L, Assert.Single(Spans(segs[1]))["core:sample_start"]);
    }

    [Fact]
    public void SegmentsShareNoMetadata()
    {
        var segs = SignalFiles.ReadSigmfCaptures<double>(Write("m",
            """[{"core:sample_start": 0}, {"core:sample_start": 3}]""", glob: ", \"x:tags\": [\"t\"]"));
        ((List<object?>)segs[0].Metadata["x:tags"]!).Add("changed");
        Assert.Equal(["t"], (List<object?>)segs[1].Metadata["x:tags"]!);
    }

    [Fact]
    public void NoCapturesIsOneSegment()
    {
        var s = Assert.Single(SignalFiles.ReadSigmfCaptures<double>(Write("n", "[]")));
        Assert.Equal([1.0, 2, 3, 4, 5, 6], Codes(s));
        Assert.Equal((0.0, 0.0), (s.CenterFrequency, s.TimeOrigin));
    }

    [Fact]
    public void ASegmentRoundTripsThroughWriteSigmf()
    {
        var seg = SignalFiles.ReadSigmfCaptures<double>(Write("w",
            """[{"core:sample_start": 0, "core:frequency": 1.0}, {"core:sample_start": 2, "core:frequency": 2.0}]"""))[1];
        string path = Path.Combine(_dir, "seg");
        SignalFiles.WriteSigmf(path, seg);
        var back = SignalFiles.ReadSigmf<double>(path);
        Assert.Equal(seg.Samples.ToArray(), back.Samples.ToArray());
        Assert.Equal((2.0, 2 / 8.0), (back.CenterFrequency, back.TimeOrigin));
    }

    [Fact]
    public void ReadSigmfNamesTheCaptureReader()
    {
        string path = Write("r", """[{"core:sample_start": 0, "core:frequency": 1.0}, {"core:sample_start": 2}]""");
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadSigmf<double>(path));
        Assert.Contains("ReadSigmfCaptures", e.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("""[{"core:sample_start": 2}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": 3}, {"core:sample_start": 3}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": 4}, {"core:sample_start": 3}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": 7}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": "3"}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": true}]""", "")]
    [InlineData("""[{"core:sample_start": 0}, {"core:sample_start": 3.0}]""", "")]
    [InlineData("""[{"core:sample_start": 0}]""", ", \"core:num_channels\": 2")]
    [InlineData("""[{"core:sample_start": 0, "core:header_bytes": 2}]""", "")]
    public void BadCapturesAreRejected(string captures, string glob)
    {
        string path = Write("b", captures, glob: glob);
        Assert.Throws<ArgumentException>(() => SignalFiles.ReadSigmfCaptures<double>(path));
    }

    [Fact]
    public void AStartAtTheEndIsAnEmptyLastSegment()
    {
        var segs = SignalFiles.ReadSigmfCaptures<double>(Write("e",
            """[{"core:sample_start": 0}, {"core:sample_start": 6}]""", """[{"core:sample_start": 6}]"""));
        Assert.Equal((6, 0, 6 / 8.0), (segs[0].Length, segs[1].Length, segs[1].TimeOrigin));
        Assert.Equal(0L, Assert.Single(Spans(segs[1]))["core:sample_start"]);
    }
}
