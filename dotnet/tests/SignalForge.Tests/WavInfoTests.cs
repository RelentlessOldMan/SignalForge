using Xunit;

namespace SignalForge.Tests;

/// <summary>WAV <c>LIST</c>/<c>INFO</c> text tags (conventions: Signal files, WAV; ADR 0091).</summary>
public sealed class WavInfoTests : IDisposable
{
    private static readonly double[] Samples = [0.5, -0.25, 0.0, 0.125];
    private static readonly Signal<double> Tone = new(Samples, 8000);
    private readonly string _dir = Directory.CreateTempSubdirectory("sfwavinfo").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    private static KeyValuePair<string, string> Tag(string id, string text) => new(id, text);

    [Fact]
    public void RoundTripKeepsOrderAndEveryPrintableCharacter()
    {
        string printable = new([.. Enumerable.Range(0x20, 0x5F).Select(c => (char)c)]);
        KeyValuePair<string, string>[] tags =
            [Tag("ISFT", "SignalForge"), Tag("ICMT", printable), Tag("INAM", ""), Tag("IAR1", new string('x', 255)), Tag("ZZZZ", "ab")];
        string path = PathOf("t.wav");
        SignalFiles.WriteWav(path, Tone, "i16", tags);
        Assert.Equal(tags, SignalFiles.ReadWavInfo(path).ToArray());
    }

    [Theory]
    [InlineData("u8")]
    [InlineData("i16")]
    [InlineData("i24")]
    [InlineData("f32")]
    [InlineData("f64")]
    public void TagsLeaveTheAudioAlone(string format)
    {
        var odd = new Signal<double>(Samples.AsSpan()[..3], 8000); // odd data sizes for u8 and i24
        string plain = PathOf("plain.wav"), tagged = PathOf("tagged.wav");
        SignalFiles.WriteWav(plain, [odd, odd], format);
        SignalFiles.WriteWav(tagged, [odd, odd], format, [Tag("INAM", "tone")]);
        Signal<double>[] a = SignalFiles.ReadWav(plain), b = SignalFiles.ReadWav(tagged);
        for (int c = 0; c < 2; c++)
            Assert.Equal(a[c].Samples.ToArray(), b[c].Samples.ToArray());
        byte[] p = File.ReadAllBytes(plain), t = File.ReadAllBytes(tagged);
        Assert.Equal(p[8..], t[8..p.Length]); // the tags only add bytes at the end
        Assert.Equal((uint)(t.Length - 8), BitConverter.ToUInt32(t, 4));
    }

    [Fact]
    public void NoOrEmptyInfoWritesThePlainFile()
    {
        SignalFiles.WriteWav(PathOf("a.wav"), Tone, "f32");
        SignalFiles.WriteWav(PathOf("b.wav"), Tone, "f32", []);
        Assert.Equal(File.ReadAllBytes(PathOf("a.wav")), File.ReadAllBytes(PathOf("b.wav")));
        Assert.Empty(SignalFiles.ReadWavInfo(PathOf("a.wav")));
    }

    [Fact]
    public void RandomTagsRoundTrip()
    {
        var rng = new Random(91);
        const string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        string path = PathOf("r.wav");
        for (int k = 0; k < 20; k++)
        {
            var ids = new HashSet<string>(Enumerable.Range(0, rng.Next(1, 8))
                .Select(_ => new string([.. Enumerable.Range(0, 4).Select(_ => alphabet[rng.Next(alphabet.Length)])])));
            KeyValuePair<string, string>[] tags = [.. ids.Select(i =>
                Tag(i, new string([.. Enumerable.Range(0, rng.Next(0, 40)).Select(_ => (char)rng.Next(0x20, 0x7F))])))];
            SignalFiles.WriteWav(path, Tone, "i16", tags);
            Assert.Equal(tags, SignalFiles.ReadWavInfo(path).ToArray());
            Assert.Equal(Samples, SignalFiles.ReadWav(path)[0].Samples.ToArray());
        }
    }

    [Theory]
    [InlineData("inam")]
    [InlineData("NAM")]
    [InlineData("INAME")]
    [InlineData("ID3 ")]
    [InlineData("")]
    [InlineData("IN-M")]
    [InlineData("INAÉ")]
    public void RejectsBadIds(string id)
    {
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.WriteWav(PathOf("x.wav"), Tone, "i16", [Tag(id, "x")]));
        Assert.Contains("info ID", e.Message, StringComparison.Ordinal);
        Assert.False(File.Exists(PathOf("x.wav")));
    }

    [Theory]
    [InlineData("café")]
    [InlineData("a\nb")]
    [InlineData("a\tb")]
    [InlineData("a\0b")]
    [InlineData("\u007f")]
    [InlineData(null)]
    public void RejectsBadText(string? text)
    {
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.WriteWav(PathOf("x.wav"), Tone, "i16", [Tag("ICMT", text!)]));
        Assert.Contains("printable ASCII", e.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void RejectsADuplicateId()
    {
        var e = Assert.Throws<ArgumentException>(() =>
            SignalFiles.WriteWav(PathOf("x.wav"), Tone, "i16", [Tag("INAM", "a"), Tag("INAM", "b")]));
        Assert.Contains("used twice", e.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("")]
    [InlineData("RIFF\0\0\0\0WAV")]
    [InlineData("RIFX\u0004\0\0\0WAVE")]
    [InlineData("RIFF\u0004\0\0\0AVI ")]
    public void RejectsFilesThatAreNotWave(string raw)
    {
        File.WriteAllBytes(PathOf("x.wav"), System.Text.Encoding.Latin1.GetBytes(raw));
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadWavInfo(PathOf("x.wav")));
        Assert.Contains("not a RIFF WAVE", e.Message, StringComparison.Ordinal);
    }
}
