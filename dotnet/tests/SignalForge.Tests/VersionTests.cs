using Xunit;

namespace SignalForge.Tests;

public class VersionTests
{
    [Fact]
    public void AssemblyVersionComesFromRepoVersionFile()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !File.Exists(Path.Combine(dir.FullName, "VERSION")))
            dir = dir.Parent;
        Assert.NotNull(dir);
        string expected = File.ReadAllText(Path.Combine(dir.FullName, "VERSION")).Trim();
        Assert.Equal(expected, typeof(Units).Assembly.GetName().Version?.ToString());
    }
}
