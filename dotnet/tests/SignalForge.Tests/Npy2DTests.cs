using System.Numerics;
using System.Text;
using Xunit;

namespace SignalForge.Tests;

/// <summary>2-D NumPy .npy files (conventions: Signal files, NumPy .npy; ADR 0092).</summary>
public sealed class Npy2DTests : IDisposable
{
    private static readonly double[] OneTwo = [1.0, 2.0];
    private readonly string _dir = Directory.CreateTempSubdirectory("sfnpy2d").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    private static byte[] File1(string header, byte[] data)
    {
        byte[] head = Encoding.ASCII.GetBytes(header + "\n");
        return [0x93, .. "NUMPY"u8, 1, 0, (byte)head.Length, 0, .. head, .. data];
    }

    [Theory]
    [InlineData(1, 1)]
    [InlineData(2, 3)]
    [InlineData(3, 2)]
    [InlineData(0, 4)]
    [InlineData(5, 0)]
    [InlineData(17, 33)]
    public void RealRoundTrip(int rows, int columns)
    {
        var rng = new Random(rows * 100 + columns);
        var x = new double[rows, columns];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < columns; j++)
                x[i, j] = rng.NextDouble() * 2 - 1;
        string path = PathOf("x.npy");
        SignalFiles.WriteNpy(path, x);
        Assert.Equal(x, SignalFiles.ReadNpy2D<double>(path));
        string header = Encoding.ASCII.GetString(File.ReadAllBytes(path), 10, 118);
        Assert.Equal($"{{'descr': '<f8', 'fortran_order': False, 'shape': ({rows}, {columns}), }}".PadRight(117) + "\n", header);
        Assert.Equal(128 + 8 * rows * columns, new FileInfo(path).Length);
    }

    [Fact]
    public void ComplexRoundTripIsRowByRow()
    {
        Complex[,] z = { { new(1, 2), new(-0.5, 0) }, { new(0, -3), new(4, 0.25) }, { Complex.Zero, new(-1, -1) } };
        string path = PathOf("z.npy");
        SignalFiles.WriteNpy(path, z);
        Assert.Equal(z, SignalFiles.ReadNpy2D<Complex>(path));
        byte[] raw = File.ReadAllBytes(path);
        Assert.Equal(-0.5, BitConverter.ToDouble(raw, 128 + 16)); // [0, 1] follows [0, 0]
        Assert.Equal(-3.0, BitConverter.ToDouble(raw, 128 + 32 + 8)); // [1, 0] imaginary part
    }

    [Fact]
    public void FortranOrderIsReadColumnByColumn()
    {
        byte[] data = [.. new short[] { 1, 4, 2, 5, 3, 6 }.SelectMany(BitConverter.GetBytes)];
        File.WriteAllBytes(PathOf("f.npy"), File1("{'descr': '<i2', 'fortran_order': True, 'shape': (2, 3), }", data));
        double[,] want = { { 1, 2, 3 }, { 4, 5, 6 } };
        Assert.Equal(want, SignalFiles.ReadNpy2D<double>(PathOf("f.npy")));
        File.WriteAllBytes(PathOf("c.npy"), File1("{'descr': '<i2', 'fortran_order': False, 'shape': (3, 2), }", data));
        double[,] wantC = { { 1, 4 }, { 2, 5 }, { 3, 6 } };
        Assert.Equal(wantC, SignalFiles.ReadNpy2D<double>(PathOf("c.npy")));
    }

    [Fact]
    public void EachReaderTakesOnlyItsOwnDimensions()
    {
        SignalFiles.WriteNpy(PathOf("one.npy"), OneTwo);
        SignalFiles.WriteNpy(PathOf("two.npy"), new double[,] { { 1.0, 2.0 } });
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadNpy2D<double>(PathOf("one.npy")));
        Assert.Contains("only 2-D", e.Message, StringComparison.Ordinal);
        e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadNpy<double>(PathOf("two.npy")));
        Assert.Contains("only 1-D", e.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void WrongElementTypeIsRejected()
    {
        SignalFiles.WriteNpy(PathOf("r.npy"), new double[,] { { 1.0 } });
        Assert.Throws<ArgumentException>(() => SignalFiles.ReadNpy2D<Complex>(PathOf("r.npy")));
        Assert.Throws<ArgumentException>(() => SignalFiles.ReadNpy2D<float>(PathOf("r.npy")));
    }

    [Theory]
    [InlineData("(2147483592, 0)")]
    [InlineData("(0, 2147483592)")]
    [InlineData("(2147483648, 0)")]
    [InlineData("(4294967296, 1)")]
    public void DimensionsBeyondTheLimitAreRejected(string shape)
    {
        File.WriteAllBytes(PathOf("big.npy"), File1($"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}", []));
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.ReadNpy2D<double>(PathOf("big.npy")));
        Assert.Contains("beyond 2147483591", e.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void LargestDimensionWithNoData()
    {
        File.WriteAllBytes(PathOf("wide.npy"), File1("{'descr': '<f8', 'fortran_order': False, 'shape': (0, 2147483591), }", []));
        double[,] got = SignalFiles.ReadNpy2D<double>(PathOf("wide.npy"));
        Assert.Equal(0, got.GetLength(0));
        Assert.Equal(Array.MaxLength, got.GetLength(1));
    }

    [Fact]
    public void NullArraysAreRejected()
    {
        Assert.Throws<ArgumentNullException>(() => SignalFiles.WriteNpy(PathOf("n.npy"), (double[,])null!));
        Assert.Throws<ArgumentNullException>(() => SignalFiles.WriteNpy(PathOf("n.npy"), (Complex[,])null!));
    }
}
