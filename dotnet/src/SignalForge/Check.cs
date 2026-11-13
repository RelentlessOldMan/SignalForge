namespace SignalForge;

/// <summary>Argument checks shared by the library.</summary>
internal static class Check
{
    /// <summary>Throws unless <paramref name="x"/> is positive and finite (NaN and infinity throw).</summary>
    public static double PositiveFinite(double x, string name) =>
        x > 0 && double.IsFinite(x) ? x : throw new ArgumentOutOfRangeException(name, x, "must be positive and finite");

    /// <summary>Throws unless <paramref name="x"/> is finite.</summary>
    public static double Finite(double x, string name) =>
        double.IsFinite(x) ? x : throw new ArgumentOutOfRangeException(name, x, "must be finite");
}
