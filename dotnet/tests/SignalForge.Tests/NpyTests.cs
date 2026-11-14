using System.Buffers.Binary;
using System.Numerics;
using System.Text;
using Xunit;

namespace SignalForge.Tests;

/// <summary>NumPy .npy files (conventions: Signal files, NumPy .npy; ADR 0056).</summary>
public sealed class NpyTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("sfnpy").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(12345)]
    public void RealRoundTrip(int n)
    {
        double[] x = [.. Enumerable.Range(0, n).Select(k => Math.Sin(k) * 1e10)];
        if (n > 0)
            x[0] = double.NaN;
        string path = PathOf("x.npy");
        SignalFiles.WriteNpy(path, x);
        Assert.Equal(128 + 8 * n, new FileInfo(path).Length);
        Assert.Equal(x, SignalFiles.ReadNpy<double>(path));
    }

    [Fact]
    public void ComplexRoundTrip()
    {
        Complex[] z = [new(1, 2), new(double.PositiveInfinity, -0.0), new(-1e-300, double.NaN)];
        string path = PathOf("z.npy");
        SignalFiles.WriteNpy(path, z);
        Complex[] got = SignalFiles.ReadNpy<Complex>(path);
        Assert.Equal(z[..2], got[..2]);
        Assert.Equal(-1e-300, got[2].Real);
        Assert.True(double.IsNaN(got[2].Imaginary));
        Assert.True(double.IsNegative(got[1].Imaginary));
    }

    [Fact]
    public void HeaderIsTheNumPyLayout()
    {
        string path = PathOf("x.npy");
        SignalFiles.WriteNpy(path, [0.5, -1.5]);
        byte[] raw = File.ReadAllBytes(path);
        Assert.Equal("\u0093NUMPY\u0001\u0000v\u0000", Encoding.Latin1.GetString(raw, 0, 10));
        Assert.Equal("{'descr': '<f8', 'fortran_order': False, 'shape': (2,), }".PadRight(117) + "\n",
            Encoding.ASCII.GetString(raw, 10, 118));
    }

    [Fact]
    public void WrongElementTypeIsRejected()
    {
        string path = PathOf("x.npy");
        SignalFiles.WriteNpy(path, [0.5]);
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadNpy<Complex>(path));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadNpy<float>(path));
        SignalFiles.WriteNpy(path, [Complex.One]);
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadNpy<double>(path));
    }

    private string File3(string header)
    {
        byte[] text = Encoding.UTF8.GetBytes(header);
        byte[] raw = [0x93, .. "NUMPY"u8, 3, 0, .. new byte[4], .. text, .. new byte[8]];
        BinaryPrimitives.WriteUInt32LittleEndian(raw.AsSpan(8), (uint)text.Length);
        string path = PathOf("h.npy");
        File.WriteAllBytes(path, raw);
        return path;
    }

    [Theory]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,),}")]
    [InlineData("{ 'descr' : '<f8' , 'fortran_order' : False , 'shape' : ( 1 , ) }\n")]
    [InlineData("{'shape':(1,),'fortran_order':True,'descr':\"<f8\"}")]
    public void HeaderSpellings(string header) => Assert.Equal([0.0], SignalFiles.ReadNpy<double>(File3(header)));

    [Theory]
    [InlineData("")]
    [InlineData("{")]
    [InlineData("{}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,)")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1 1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':[1]}")]
    [InlineData("{'descr':'<f8','fortran_order':Falsey,'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':false,'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':None,'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,)}}")]
    [InlineData("{'descr':'<f8'\"fortran_order\":False,'shape':(1,)}")]
    [InlineData("{'descr':'<f8\",'fortran_order':False,'shape':(1,)}")]
    [InlineData("{descr:'<f8','fortran_order':False,'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,),'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':'(1,)'}")]
    [InlineData("{'descr':True,'fortran_order':False,'shape':(1,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(١,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(99999999999999999999999,)}")]
    [InlineData("{'descr':'<f8','fortran_order':False,'shape':(1,)}\0")]
    public void BadHeaders(string header) =>
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadNpy<double>(File3(header)));

    [Fact]
    public void MissingFileIsAnIOError() =>
        Assert.ThrowsAny<IOException>(() => SignalFiles.ReadNpy<double>(PathOf("missing.npy")));
}
