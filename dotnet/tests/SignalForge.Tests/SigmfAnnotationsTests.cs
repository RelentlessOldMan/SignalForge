using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>SigMF annotations as the metadata key core:annotations (conventions: Signal files; ADR 0061).</summary>
public sealed class SigmfAnnotationsTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string P(string name) => Path.Combine(_dir, name);

    private static Signal<double> Sig(object? annotations) => new(
        [.. Enumerable.Range(0, 8).Select(i => i / 16.0)], 1000,
        metadata: new Dictionary<string, object?> { ["core:annotations"] = annotations, ["run"] = 1 });

    private static Dictionary<string, object?> Span(params (string Key, object? Value)[] fields) =>
        fields.ToDictionary(f => f.Key, f => f.Value);

    [Fact]
    public void RoundTripAndLayout()
    {
        object[] spans =
        [
            Span(("core:sample_start", 2), ("core:sample_count", 3), ("core:label", "burst")),
            Span(("core:sample_start", 2L), ("core:comment", "same start")),
            Span(("core:sample_start", (byte)7), ("x:score", 0.5)),
        ];
        SignalFiles.WriteSigmf(P("a"), Sig(spans));
        using (var doc = JsonDocument.Parse(File.ReadAllText(P("a.sigmf-meta"))))
        {
            Assert.False(doc.RootElement.GetProperty("global").TryGetProperty("core:annotations", out _));
            Assert.Equal(3, doc.RootElement.GetProperty("annotations").GetArrayLength());
        }
        var r = (List<object?>)SignalFiles.ReadSigmf<double>(P("a")).Metadata["core:annotations"]!;
        var first = (Dictionary<string, object?>)r[0]!;
        Assert.Equal((2L, 3L, "burst"), (first["core:sample_start"], first["core:sample_count"], first["core:label"]));
        Assert.Equal(7L, ((Dictionary<string, object?>)r[2]!)["core:sample_start"]);
        Assert.Equal(0.5, ((Dictionary<string, object?>)r[2]!)["x:score"]);
    }

    [Fact]
    public void EmptyListReadsBackAsNoKey()
    {
        SignalFiles.WriteSigmf(P("e"), Sig(Array.Empty<object>()));
        var m = SignalFiles.ReadSigmf<double>(P("e")).Metadata;
        Assert.False(m.ContainsKey("core:annotations"));
        Assert.Equal(1L, m["run"]);
    }

    [Fact]
    public void SpanPastTheSamplesIsKept()
    {
        SignalFiles.WriteSigmf(P("f"), Sig(new object[] { Span(("core:sample_start", 100), ("core:sample_count", 50)) }));
        var r = (List<object?>)SignalFiles.ReadSigmf<double>(P("f")).Metadata["core:annotations"]!;
        Assert.Equal(100L, ((Dictionary<string, object?>)r[0]!)["core:sample_start"]);
    }

    public static TheoryData<object?> Bad() =>
    [
        null,
        Span(("core:sample_start", 0)),
        "spans",
        new object[] { 5 },
        new object[] { Span(("core:label", "no start")) },
        new object[] { Span(("core:sample_start", 1.0)) },
        new object[] { Span(("core:sample_start", true)) },
        new object[] { Span(("core:sample_start", -1)) },
        new object[] { Span(("core:sample_start", 0), ("core:sample_count", -1L)) },
        new object[] { Span(("core:sample_start", 0), ("core:sample_count", 2.5)) },
        new object[] { Span(("core:sample_start", ulong.MaxValue)) },
        new object[] { Span(("core:sample_start", 3)), Span(("core:sample_start", 2)) },
        new object[] { Span(("core:sample_start", 0), ("x:bad", double.NaN)) },
    ];

    [Theory]
    [MemberData(nameof(Bad))]
    public void WriteRejects(object? annotations)
    {
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("w"), Sig(annotations)));
        Assert.False(File.Exists(P("w.sigmf-meta")));
    }
}
