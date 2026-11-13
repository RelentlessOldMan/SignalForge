using System.Text.Json;

namespace SignalForge.Tests;

public class ConformanceTests
{
    private static readonly Dictionary<string, Conformance.VectorCase> Cases =
        Conformance.LoadCases().ToDictionary(c => c.ToString());

    public static TheoryData<string> CaseNames() => new(Cases.Keys);

    [Theory]
    [MemberData(nameof(CaseNames))]
    public void Vector(string name)
    {
        var messages = Conformance.Run(Cases[name]);
        Assert.True(messages.Count == 0, string.Join("; ", messages));
    }

    [Fact]
    public void EveryCaseHasASource() =>
        Assert.All(Cases.Values, c =>
            Assert.False(string.IsNullOrEmpty(c.Json.GetProperty("source").GetString()), c.Id));

    [Fact]
    public void ComparisonCatchesAWrongValue()
    {
        using var doc = JsonDocument.Parse(
            """{"id": "x", "op": "lin_to_db", "args": {"x": 10}, "expected": 10.001, "source": "t"}""");
        Assert.NotEmpty(Conformance.Run(new Conformance.VectorCase("t.json", "x", doc.RootElement.Clone())));
    }
}
