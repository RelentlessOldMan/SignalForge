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

    private static readonly Dictionary<string, Conformance.VectorCase> SelfTest =
        Conformance.LoadCases(Path.Combine(Conformance.VectorsDir(), "..", "selftest")).ToDictionary(c => c.Id);

    public static TheoryData<string> SelfTestNames() => new(SelfTest.Keys);

    /// <summary>Every case in vectors/selftest is wrong; the runner must fail it, not pass or crash.</summary>
    [Theory]
    [MemberData(nameof(SelfTestNames))]
    public void RunnerFailsAWrongCase(string id) =>
        Assert.True(Conformance.Run(SelfTest[id]).Count > 0, SelfTest[id].Json.GetProperty("why").GetString());
}
