using System.Buffers.Binary;
using Xunit;

namespace SignalForge.Tests;

/// <summary>WAV cue points, their <c>LIST</c>/<c>adtl</c> labels and regions (conventions: Signal files, WAV;
/// ADR 0094, 0095).</summary>
public sealed class WavCuesTests : IDisposable
{
    private static readonly double[] Samples = [0.5, -0.25, 0.0, 0.125];
    private static readonly Signal<double> Tone = new(Samples, 8000);
    private readonly string _dir = Directory.CreateTempSubdirectory("sfwavcues").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    [Fact]
    public void RoundTripKeepsOrderPositionsAndLabels()
    {
        string printable = new([.. Enumerable.Range(0x20, 0x5F).Select(c => (char)c)]);
        (long, long, string)[] cues = [(4, 0, "end"), (0, 4, ""), (2, 0, printable), (2, 2, "again"), (1, 1, "")];
        string path = PathOf("c.wav");
        SignalFiles.WriteWav(path, Tone, "i16", cues: cues);
        Assert.Equal(cues, SignalFiles.ReadWavCues(path));
    }

    [Theory]
    [InlineData("u8")]
    [InlineData("i16")]
    [InlineData("i24")]
    [InlineData("f32")]
    [InlineData("f64")]
    public void CuesLeaveTheAudioAndTagsAlone(string format)
    {
        var odd = new Signal<double>(Samples.AsSpan()[..3], 8000);
        KeyValuePair<string, string>[] tags = [new("INAM", "tone")];
        (long, long, string)[] cues = [(1, 2, "one"), (3, 0, "")];
        SignalFiles.WriteWav(PathOf("plain.wav"), [odd, odd], format, tags);
        SignalFiles.WriteWav(PathOf("marked.wav"), [odd, odd], format, tags, cues);
        var a = SignalFiles.ReadWav(PathOf("plain.wav"));
        var b = SignalFiles.ReadWav(PathOf("marked.wav"));
        for (int c = 0; c < 2; c++)
            Assert.Equal(a[c].Samples.ToArray(), b[c].Samples.ToArray());
        Assert.Equal(tags, SignalFiles.ReadWavInfo(PathOf("marked.wav")).ToArray());
        Assert.Equal(cues, SignalFiles.ReadWavCues(PathOf("marked.wav")));
        byte[] raw = File.ReadAllBytes(PathOf("marked.wav"));
        Assert.Equal((uint)(raw.Length - 8), BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(4)));
    }

    [Fact]
    public void NoOrEmptyCuesWriteAPlainFile()
    {
        SignalFiles.WriteWav(PathOf("a.wav"), Tone, "i16");
        SignalFiles.WriteWav(PathOf("b.wav"), Tone, "i16", cues: []);
        Assert.Equal(File.ReadAllBytes(PathOf("a.wav")), File.ReadAllBytes(PathOf("b.wav")));
        Assert.Empty(SignalFiles.ReadWavCues(PathOf("a.wav")));
    }

    [Theory]
    [InlineData(-1, 0, "")]
    [InlineData(5, 0, "")]
    [InlineData(long.MaxValue, 0, "")]
    [InlineData(0, -1, "")]
    [InlineData(1, 4, "")]
    [InlineData(4, 1, "")]
    [InlineData(1, long.MaxValue, "")]
    [InlineData(0, 0, "caf\u00e9")]
    [InlineData(0, 0, "\t")]
    [InlineData(0, 0, null)]
    public void BadCuesAreRejected(long position, long length, string? label)
    {
        var e = Assert.Throws<ArgumentException>(() =>
            SignalFiles.WriteWav(PathOf("c.wav"), Tone, "i16", cues: [(position, length, label!)]));
        Assert.Equal("cues", e.ParamName);
        Assert.False(File.Exists(PathOf("c.wav")));
    }

    [Fact]
    public void ARegionIsOneLtxtAfterItsLabl()
    {
        SignalFiles.WriteWav(PathOf("r.wav"), Tone, "i16", cues: [(1, 3, "ab")]);
        byte[] raw = File.ReadAllBytes(PathOf("r.wav"));
        int at = raw.AsSpan().IndexOf("adtl"u8);
        byte[] want =
        [
            .. "adtllabl"u8, 7, 0, 0, 0, 1, 0, 0, 0, .. "ab"u8, 0, 0,
            .. "ltxt"u8, 20, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 0, .. "rgn "u8, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        Assert.Equal(want, raw[at..]);
    }

    [Fact]
    public void AFileThatIsNotWaveIsRejected()
    {
        File.WriteAllBytes(PathOf("x.wav"), [.. "RIFF"u8, 4, 0, 0, 0, .. "WAV"u8]);
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadWavCues(PathOf("x.wav")));
        Assert.Equal("path", e.ParamName);
    }
}
