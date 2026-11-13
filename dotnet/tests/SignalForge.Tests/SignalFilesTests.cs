using System.Numerics;
using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Signal files: round trips, metadata mapping, write errors (conventions: Signal files).</summary>
public sealed class SignalFilesTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string P(string name) => Path.Combine(_dir, name);

    public static TheoryData<string> Types()
    {
        var t = new TheoryData<string>();
        foreach (char k in "cr")
        {
            foreach (string ty in (string[])["f64", "f32", "i32", "i16"])
            {
                t.Add($"{k}{ty}_le");
                t.Add($"{k}{ty}_be");
            }
            t.Add($"{k}i8");
        }
        return t;
    }

    private static double Step(string datatype) => datatype[1..Math.Min(4, datatype.Length)] switch
    {
        "f64" => 0,
        "f32" => Math.ScaleB(1, -24),
        "i32" => Math.ScaleB(1, -31),
        "i16" => Math.ScaleB(1, -15),
        _ => Math.ScaleB(1, -7),
    };

    [Theory]
    [MemberData(nameof(Types))]
    public void RoundTripEveryDatatype(string datatype)
    {
        var rng = new Random(1);
        double U() => rng.NextDouble() * 1.98 - 0.99;
        if (datatype[0] == 'c')
        {
            Complex[] x = [.. Enumerable.Range(0, 64).Select(_ => new Complex(U(), U()))];
            SignalFiles.WriteSigmf(P("r"), new Signal<Complex>(x, 1e3), datatype);
            var y = SignalFiles.ReadSigmf<Complex>(P("r")).Samples.ToArray();
            Assert.All(x.Zip(y), p => Assert.True(Math.Max(Math.Abs(p.First.Real - p.Second.Real), Math.Abs(p.First.Imaginary - p.Second.Imaginary)) <= Step(datatype)));
            Assert.Equal(SignalFiles.EncodeSamples(x, datatype).Length, new FileInfo(P("r.sigmf-data")).Length);
        }
        else
        {
            double[] x = [.. Enumerable.Range(0, 64).Select(_ => U())];
            SignalFiles.WriteSigmf(P("r"), new Signal<double>(x, 1e3), datatype);
            var y = SignalFiles.ReadSigmf<double>(P("r")).Samples.ToArray();
            Assert.All(x.Zip(y), p => Assert.True(Math.Abs(p.First - p.Second) <= Step(datatype)));
        }
    }

    [Fact]
    public void FieldsAndMetadataRoundTrip()
    {
        var meta = new Dictionary<string, object?>
        {
            ["core:author"] = "me",
            ["run"] = 3,
            ["gains"] = new object[] { 1, 2.5 },
            ["nested"] = new Dictionary<string, object?> { ["a"] = null },
        };
        var s = new Signal<Complex>([new Complex(1, 1), new Complex(0, -0.5)], 2.5e6, 915e6, -1.25, "V", 50, meta);
        SignalFiles.WriteSigmf(P("x.sigmf-meta"), s);
        var r = SignalFiles.ReadSigmf<Complex>(P("x.sigmf-data"));
        Assert.Equal(s.Samples.ToArray(), r.Samples.ToArray());
        Assert.Equal((2.5e6, 915e6, -1.25, "V", (double?)50), (r.SampleRate, r.CenterFrequency, r.TimeOrigin, r.Units, r.Impedance));
        Assert.Equal("me", r.Metadata["core:author"]);
        Assert.Equal(3L, r.Metadata["run"]);
        Assert.Equal([1L, 2.5], (List<object?>)r.Metadata["gains"]!);
        Assert.Null(((Dictionary<string, object?>)r.Metadata["nested"]!)["a"]);
        using var doc = JsonDocument.Parse(File.ReadAllText(P("x.sigmf-meta")));
        var glob = doc.RootElement.GetProperty("global");
        Assert.Equal("cf64_le", glob.GetProperty("core:datatype").GetString());
        Assert.Equal("2500000.0", glob.GetProperty("core:sample_rate").GetRawText());
    }

    [Fact]
    public void EmptySignal()
    {
        SignalFiles.WriteSigmf(P("e"), new Signal<Complex>([], 1), "ci16_le");
        Assert.Equal(0, SignalFiles.ReadSigmf<Complex>(P("e")).Length);
    }

    [Fact]
    public void WrongKindIsRejected()
    {
        SignalFiles.WriteSigmf(P("k"), new Signal<double>([0.5], 1));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadSigmf<Complex>(P("k")));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.DecodeSamples<float>([0, 0, 0, 0], "rf32_le"));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("k"), new Signal<double>([0.5], 1), "cf32_le"));
    }

    [Theory]
    [InlineData("core:sample_rate", 2)]
    [InlineData("signalforge:x", 1)]
    [InlineData("bad", double.NaN)]
    public void WriteRejectsBadMetadata(string key, object value) =>
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { [key] = value })));

    [Fact]
    public void WriteRejectsNonJsonAndNonFinite()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { ["o"] = new object() })));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, double.PositiveInfinity)));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, 0, double.NaN)));
    }

    [Fact]
    public void MissingFileIsAnIoError() =>
        Assert.Throws<FileNotFoundException>(() => SignalFiles.ReadSigmf<double>(P("absent")));
}
