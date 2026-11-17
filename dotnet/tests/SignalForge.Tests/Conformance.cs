using System.Globalization;
using System.Numerics;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace SignalForge.Tests;

/// <summary>Loads and runs the shared vectors in vectors/cases. Format: vectors/README.md.</summary>
public static class Conformance
{
    private const double DefaultAbs = 1e-12, DefaultRel = 1e-12;

    public sealed record VectorCase(string File, string Id, JsonElement Json)
    {
        public override string ToString() => $"{File}:{Id}";
    }

    public static string VectorsDir()
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d is not null; d = d.Parent)
        {
            string cand = Path.Combine(d.FullName, "vectors", "cases");
            if (Directory.Exists(cand))
                return cand;
        }
        throw new DirectoryNotFoundException("vectors/cases not found above " + AppContext.BaseDirectory);
    }

    public static IEnumerable<VectorCase> LoadCases(string? dir = null)
    {
        foreach (string path in Directory.GetFiles(dir ?? VectorsDir(), "*.json").Order(StringComparer.Ordinal))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            if (root.GetProperty("schema").GetInt32() != 1)
                throw new InvalidDataException($"{Path.GetFileName(path)}: unsupported schema");
            foreach (var c in root.GetProperty("cases").EnumerateArray())
                yield return new VectorCase(Path.GetFileName(path), c.GetProperty("id").GetString()!, c.Clone());
        }
    }

    /// <summary>Runs one case; returns the failure messages (empty when it passes).</summary>
    public static List<string> Run(VectorCase c) => RunWithActual(c).Messages;

    /// <summary>Runs one case; returns the failure messages and the result in canonical form (null
    /// when the operation threw).</summary>
    public static (List<string> Messages, object? Actual) RunWithActual(VectorCase c)
    {
        object? actual = null;
        try
        {
            return (RunCase(c.Json, out actual), actual);
        }
        catch (InvalidDataException e)
        {
            return ([$"bad case: {e.Message}"], actual);
        }
    }

    /// <summary>Runs every case and writes the report that <c>python -m signalforge.conformance
    /// --report</c> writes: implementation, passed, failed, and per case file, id, passed, messages
    /// and the actual result (no file when <paramref name="path"/> is null). Returns the number of
    /// failures.</summary>
    public static int WriteReport(string? path, string? dir = null, TextWriter? log = null)
    {
        var cases = new JsonArray();
        int passed = 0, failed = 0;
        foreach (var c in LoadCases(dir))
        {
            var (msgs, actual) = RunWithActual(c);
            if (msgs.Count == 0)
                passed++;
            else
            {
                failed++;
                log?.WriteLine($"FAIL {c.File} {c.Id}: {string.Join("; ", msgs)}");
            }
            cases.Add(new JsonObject
            {
                ["file"] = c.File,
                ["id"] = c.Id,
                ["passed"] = msgs.Count == 0,
                ["messages"] = new JsonArray([.. msgs.Select(m => (JsonNode?)JsonValue.Create(m))]),
                ["actual"] = Encode(actual),
            });
        }
        log?.WriteLine($"{passed}/{passed + failed} cases passed");
        if (path is null)
            return failed;
        var report = new JsonObject { ["implementation"] = "dotnet", ["passed"] = passed, ["failed"] = failed, ["cases"] = cases };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        File.WriteAllText(path, report.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        return failed;
    }

    /// <summary>Canonical result to the JSON vector form: non-finite numbers as "inf", "-inf",
    /// "nan"; complex values as {"re", "im"}.</summary>
    public static JsonNode? Encode(object? v) => v switch
    {
        null => null,
        double d => double.IsFinite(d) ? JsonValue.Create(d) : JsonValue.Create(double.IsNaN(d) ? "nan" : d > 0 ? "inf" : "-inf"),
        bool b => JsonValue.Create(b),
        string s => JsonValue.Create(s),
        Complex z => new JsonObject { ["re"] = Encode(z.Real), ["im"] = Encode(z.Imaginary) },
        Complex[] zs => new JsonObject
        {
            ["re"] = new JsonArray([.. zs.Select(z => Encode(z.Real))]),
            ["im"] = new JsonArray([.. zs.Select(z => Encode(z.Imaginary))]),
        },
        double[] ds => new JsonArray([.. ds.Select(d => Encode(d))]),
        double[][] rows => new JsonArray([.. rows.Select(r => Encode(r))]),
        Dictionary<string, object?> m => new JsonObject(m.Select(kv => KeyValuePair.Create(kv.Key, Encode(kv.Value)))),
        List<object?> l => new JsonArray([.. l.Select(Encode)]),
        _ => throw new InvalidOperationException($"cannot encode {v.GetType()}"),
    };

    private static List<string> RunCase(JsonElement json, out object? canonical)
    {
        canonical = null;
        string op = json.GetProperty("op").GetString()!;
        var args = new Dictionary<string, object?>();
        var fractional = new HashSet<string>(); // numbers written with a point or exponent
        if (json.TryGetProperty("args", out var a))
            foreach (var p in a.EnumerateObject())
            {
                args[p.Name] = Decode(p.Value);
                if (p.Value.ValueKind == JsonValueKind.Number && p.Value.GetRawText().IndexOfAny(['.', 'e', 'E']) >= 0)
                    fractional.Add(p.Name);
            }
        double abs = DefaultAbs, rel = DefaultRel;
        if (json.TryGetProperty("tol", out var tol))
        {
            if (tol.TryGetProperty("abs", out var t)) abs = t.GetDouble();
            if (tol.TryGetProperty("rel", out t)) rel = t.GetDouble();
        }
        bool wantError = json.TryGetProperty("error", out var err);

        object? actual;
        try
        {
            actual = Invoke(op, new Args(args, fractional));
            canonical = Canonical(actual);
        }
        catch (LibraryArgumentException e)
        {
            return wantError && err.GetString() == "invalid_argument"
                ? []
                : [$"threw {e.InnerException!.GetType().Name}: {e.InnerException.Message}"];
        }
        if (wantError)
            return [$"expected error {err.GetString()}"];
        var msgs = new List<string>();
        if (!json.TryGetProperty("expected", out var expected))
            throw new InvalidDataException("no expected value or error");
        Compare(canonical, Decode(expected), abs, rel, "", msgs);
        return msgs;
    }

    /// <summary>An ArgumentException thrown by the library itself (not by argument decoding).</summary>
    private sealed class LibraryArgumentException(ArgumentException inner) : Exception(inner.Message, inner);

    /// <summary>A case's arguments. Every argument must be read exactly once, so a misspelled one fails.
    /// An integer argument must be written as a JSON integer: Python rejects 2.0 where it wants an
    /// int, and the C# API cannot be given one, so such a case could only pass in one language.</summary>
    private sealed class Args(Dictionary<string, object?> a, HashSet<string>? fractional = null)
    {
        private readonly HashSet<string> _unused = [.. a.Keys];

        public bool Has(string k) => a.ContainsKey(k);

        public object? Get(string k)
        {
            if (!a.TryGetValue(k, out var v))
                throw new InvalidDataException($"missing argument {k}");
            _unused.Remove(k);
            return v;
        }

        public double D(string k) => Get(k) as double? ?? throw new InvalidDataException($"{k} must be a number");

        public double Opt(string k, double dflt) => Has(k) ? D(k) : dflt;

        public double? OptD(string k) => Has(k) ? D(k) : null;

        public int I(string k)
        {
            double v = D(k);
            if (fractional?.Contains(k) == true)
                throw new InvalidDataException($"{k} must be written as a JSON integer, got {v}");
            return v == Math.Floor(v) && v is >= int.MinValue and <= int.MaxValue
                ? (int)v
                : throw new InvalidDataException($"{k} must be an integer, got {v}");
        }

        public int? OptInt(string k) => Has(k) ? I(k) : null;

        public bool Flag(string k, bool dflt = false) =>
            !Has(k) ? dflt : Get(k) as bool? ?? throw new InvalidDataException($"{k} must be true or false");

        public void CheckAllUsed()
        {
            if (_unused.Count > 0)
                throw new InvalidDataException($"unknown argument(s): {string.Join(", ", _unused)}");
        }
    }

    private static object? Invoke(string op, Args a)
    {
        Func<object?> call = op switch
        {
            "lin_to_db" => Bind(a.D("ratio"), Units.LinToDb),
            "db_to_lin" => Bind(a.D("db"), Units.DbToLin),
            "amp_to_db" => Bind(a.D("ratio"), Units.AmpToDb),
            "db_to_amp" => Bind(a.D("db"), Units.DbToAmp),
            "hz_to_mel" => Bind((a.D("hz"), Mel(a)), t => Units.HzToMel(t.Item1, t.Item2)),
            "mel_to_hz" => Bind((a.D("mel"), Mel(a)), t => Units.MelToHz(t.Item1, t.Item2)),
            "hz_to_erb_rate" => Bind(a.D("hz"), Units.HzToErbRate),
            "erb_rate_to_hz" => Bind(a.D("erb"), Units.ErbRateToHz),
            "erb_bandwidth" => Bind(a.D("hz"), Units.ErbBandwidth),
            "octave_bands" => Bind((a.I("fraction"), a.D("min_frequency"), a.D("max_frequency")), t => Units.OctaveBands(t.Item1, t.Item2, t.Item3)),
            "a_weighting" => Bind(a.D("frequency"), Units.AWeighting),
            "c_weighting" => Bind(a.D("frequency"), Units.CWeighting),
            "hz_to_bark" => Bind(a.D("hz"), Units.HzToBark),
            "bark_to_hz" => Bind(a.D("bark"), Units.BarkToHz),
            "erb_space" => Bind((a.D("min_frequency"), a.D("max_frequency"), a.I("n_frequencies")), t => Units.ErbSpace(t.Item1, t.Item2, t.Item3)),
            "w_to_dbm" => Bind(a.D("watts"), Units.WToDbm),
            "dbm_to_w" => Bind(a.D("dbm"), Units.DbmToW),
            "vrms_to_dbm" => Bind((a.D("vrms"), a.Opt("impedance", Units.DefaultImpedance)), t => Units.VrmsToDbm(t.Item1, t.Item2)),
            "dbm_to_vrms" => Bind((a.D("dbm"), a.Opt("impedance", Units.DefaultImpedance)), t => Units.DbmToVrms(t.Item1, t.Item2)),
            "tone" => Tone(a),
            "prbs" => Prbs(a),
            "multitone" => Multitone(a),
            "newman_phases" => Bind(a.I("count"), Waveforms.NewmanPhases),
            "chirp" => Chirp(a),
            "pulse_train" => Bind((a.I("num_samples"), a.I("period"), a.I("width"), a.Opt("amplitude", 1), a.Has("delay") ? a.I("delay") : 0),
                t => Waveforms.PulseTrain(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "temporal_centroid" => a.Get("samples") is Complex[]? Bind((Complexes(a.Get("samples")), a.D("sample_rate")), t => Measurements.TemporalCentroid(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate")), t => Measurements.TemporalCentroid(t.Item1, t.Item2)),
            "bass_ratio" => Bind(Reals(a.Get("times")), t => Measurements.BassRatio(t)),
            "treble_ratio" => Bind(Reals(a.Get("times")), t => Measurements.TrebleRatio(t)),
            "stage_support" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate"), a.Flag("late", false)), t => Measurements.StageSupport(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate"), a.Flag("late", false)), t => Measurements.StageSupport(t.Item1, t.Item2, t.Item3)),
            "sound_strength" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), Complexes(a.Get("reference"))), t => Measurements.SoundStrength(t.Item1, t.Item2))
                : Bind((Reals(a.Get("impulse_response")), Reals(a.Get("reference"))), t => Measurements.SoundStrength(t.Item1, t.Item2)),
            "speech_transmission_index" => Bind(Rows(a.Get("mtf")), Measurements.SpeechTransmissionIndex),
            "modulation_transfer" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate"), Reals(a.Get("frequencies"))), t => Measurements.ModulationTransfer(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate"), Reals(a.Get("frequencies"))), t => Measurements.ModulationTransfer(t.Item1, t.Item2, t.Item3)),
            "lateral_fraction" => Bind((Reals(a.Get("omni")), Reals(a.Get("figure_eight")), a.D("sample_rate"), a.Opt("start", 0.005), a.Opt("stop", 0.08)), t => Measurements.LateralFraction(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "iacc" => Bind((Reals(a.Get("left")), Reals(a.Get("right")), a.D("sample_rate"), a.Opt("max_lag", 0.001)), t => Measurements.Iacc(t.Item1, t.Item2, t.Item3, t.Item4)),
            "centre_time" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.CentreTime(t.Item1, t.Item2))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.CentreTime(t.Item1, t.Item2)),
            "clarity" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("time", 0.08)), t => Measurements.Clarity(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("time", 0.08)), t => Measurements.Clarity(t.Item1, t.Item2, t.Item3)),
            "definition" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("time", 0.05)), t => Measurements.Definition(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("time", 0.05)), t => Measurements.Definition(t.Item1, t.Item2, t.Item3)),
            "schroeder_decay" => a.Get("impulse_response") is Complex[]? Bind(Complexes(a.Get("impulse_response")), h => Measurements.SchroederDecay(h))
                : Bind(Reals(a.Get("impulse_response")), h => Measurements.SchroederDecay(h)),
            "gcc_phat" => Bind((Reals(a.Get("x")), Reals(a.Get("y")), a.D("sample_rate"), a.OptD("max_delay")), t => Measurements.GccPhat(t.Item1, t.Item2, t.Item3, t.Item4)),
            "energy_separation" => Bind((Reals(a.Get("samples")), a.D("sample_rate")), t => Measurements.EnergySeparation(t.Item1, t.Item2)),
            "teager_energy" => a.Get("samples") is Complex[]? Bind(Complexes(a.Get("samples")), x => Measurements.TeagerEnergy(x))
                : Bind(Reals(a.Get("samples")), x => Measurements.TeagerEnergy(x)),
            "energy_time_curve" => Bind(Reals(a.Get("impulse_response")), h => Measurements.EnergyTimeCurve(h)),
            "decay_time" => Bind((Reals(a.Get("decay")), a.D("sample_rate"), a.Opt("start_db", -5.0), a.Opt("stop_db", -25.0)), t => Measurements.DecayTime(t.Item1, t.Item2, t.Item3, t.Item4)),
            "noise_compensated_decay" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.Opt("tail", 0.1)), t => Measurements.NoiseCompensatedDecay(t.Item1, t.Item2))
                : Bind((Reals(a.Get("impulse_response")), a.Opt("tail", 0.1)), t => Measurements.NoiseCompensatedDecay(t.Item1, t.Item2)),
            "decay_curvature" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.DecayCurvature(t.Item1, t.Item2))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.DecayCurvature(t.Item1, t.Item2)),
            "early_decay_time" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.EarlyDecayTime(t.Item1, t.Item2))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate")), t => Measurements.EarlyDecayTime(t.Item1, t.Item2)),
            "reverberation_time" => a.Get("impulse_response") is Complex[]? Bind((Complexes(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("start_db", -5.0), a.Opt("stop_db", -25.0)),
                    t => Measurements.ReverberationTime(t.Item1, t.Item2, t.Item3, t.Item4))
                : Bind((Reals(a.Get("impulse_response")), a.D("sample_rate"), a.Opt("start_db", -5.0), a.Opt("stop_db", -25.0)),
                    t => Measurements.ReverberationTime(t.Item1, t.Item2, t.Item3, t.Item4)),
            "block_leq" => a.Get("samples") is Complex[]? Bind((Complexes(a.Get("samples")), a.D("sample_rate"), a.D("duration")), t => Measurements.BlockLeq(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate"), a.D("duration")), t => Measurements.BlockLeq(t.Item1, t.Item2, t.Item3)),
            "sound_exposure" => a.Get("samples") is Complex[]? Bind((Complexes(a.Get("samples")), a.D("sample_rate")), t => Measurements.SoundExposure(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate")), t => Measurements.SoundExposure(t.Item1, t.Item2)),
            "exceedance_levels" => Bind((Reals(a.Get("powers")), Reals(a.Get("percents"))), t => Measurements.ExceedanceLevels(t.Item1, t.Item2)),
            "octave_band_levels" => a.Get("samples") is Complex[]? Bind((Complexes(a.Get("samples")), a.D("sample_rate"), a.I("fraction"), a.D("min_frequency"), a.D("max_frequency"), a.OptInt("order") ?? 3),
                    t => Measurements.OctaveBandLevels(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate"), a.I("fraction"), a.D("min_frequency"), a.D("max_frequency"), a.OptInt("order") ?? 3),
                    t => Measurements.OctaveBandLevels(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "time_weighting" => a.Get("samples") is Complex[]? Bind((Complexes(a.Get("samples")), a.D("sample_rate"), a.D("time_constant")), t => Measurements.TimeWeighting(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate"), a.D("time_constant")), t => Measurements.TimeWeighting(t.Item1, t.Item2, t.Item3)),
            "autocorrelation_pitch" => Bind((Reals(a.Get("samples")), a.D("sample_rate"), a.D("min_frequency"), a.D("max_frequency")),
                t => Measurements.AutocorrelationPitch(t.Item1, t.Item2, t.Item3, t.Item4)),
            "cepstrum_pitch" => Bind((Reals(a.Get("samples")), a.D("sample_rate"), a.D("min_frequency"), a.D("max_frequency"), a.Has("nfft") ? a.I("nfft") : (int?)null),
                t => Measurements.CepstrumPitch(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "zero_crossing_rate" => Bind(Reals(a.Get("samples")), x => Measurements.ZeroCrossingRate(x)),
            "power_stats" => a.Get("samples") is Complex[] cs
                ? () => Measurements.PowerStats(cs)
                : Bind(Reals(a.Get("samples")), x => Measurements.PowerStats(x)),
            "kay_frequency" => Bind((Complexes(a.Get("samples")), a.D("sample_rate")), t => Measurements.KayFrequency(t.Item1, t.Item2)),
            "power_ccdf" => a.Get("samples") is Complex[] cc
                ? Bind(Reals(a.Get("levels_db")), l => Measurements.PowerCcdf(cc, l))
                : Bind((Reals(a.Get("samples")), Reals(a.Get("levels_db"))), t => Measurements.PowerCcdf(t.Item1, t.Item2)),
            "power_ccdf_level" => a.Get("samples") is Complex[] cl
                ? Bind(a.D("probability"), q => Measurements.PowerCcdfLevel(cl, q))
                : Bind((Reals(a.Get("samples")), a.D("probability")), t => Measurements.PowerCcdfLevel(t.Item1, t.Item2)),
            "tone_metrics" => ToneMetricsOp(a),
            "sfdr" => SfdrOp(a),
            "two_tone_imd" => TwoToneImdOp(a),
            "two_tone_ip2" => TwoToneIp2Op(a),
            "two_tone_ip5" => TwoToneIp5Op(a),
            "phase_noise_ssb" => PhaseNoiseSsbOp(a),
            "integrated_phase_noise" => IntegratedPhaseNoiseOp(a),
            "phase_noise_spurs" => PhaseNoiseSpursOp(a),
            "noise_figure_cascade" => Bind((Reals(a.Get("noise_figures_db")), Reals(a.Get("gains_db"))), t => Measurements.NoiseFigureCascade(t.Item1, t.Item2)),
            "am_am_pm" => Bind((Complexes(a.Get("input")), Complexes(a.Get("output")), Reals(a.Get("edges_db"))),
                t => Measurements.AmAmPm(t.Item1, t.Item2, t.Item3)),
            "gain_compression" => Bind((Reals(a.Get("input_db")), Reals(a.Get("output_db")), a.Opt("compression_db", 1.0), a.OptInt("linear_points") ?? 1),
                t => Measurements.GainCompression(t.Item1, t.Item2, t.Item3, t.Item4)),
            "noise_figure_y_factor" => Bind((a.D("hot_power"), a.D("cold_power"), a.D("enr_db"), a.Has("cold_temperature") ? a.D("cold_temperature") : 290), t => Measurements.NoiseFigureYFactor(t.Item1, t.Item2, t.Item3, t.Item4)),
            "qpsk_map" => Bind(Bits(a.Get("bits")), b => Modulation.QpskMap(b)),
            "qpsk_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.QpskDemapHard(s)),
            "qpsk_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.QpskDemapLlr(t.Item1, t.Item2)),
            "psk8_map" => Bind(Bits(a.Get("bits")), b => Modulation.Psk8Map(b)),
            "psk8_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.Psk8DemapHard(s)),
            "psk8_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.Psk8DemapLlr(t.Item1, t.Item2)),
            "qam16_map" => Bind(Bits(a.Get("bits")), b => Modulation.Qam16Map(b)),
            "qam16_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.Qam16DemapHard(s)),
            "qam16_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.Qam16DemapLlr(t.Item1, t.Item2)),
            "qam64_map" => Bind(Bits(a.Get("bits")), b => Modulation.Qam64Map(b)),
            "qam64_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.Qam64DemapHard(s)),
            "qam64_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.Qam64DemapLlr(t.Item1, t.Item2)),
            "ofdm_modulate" => Bind((Complexes(a.Get("symbols")), a.I("nfft"), a.I("cp_len"), a.Has("subcarriers") ? Ints(a.Get("subcarriers")) : null),
                t => Modulation.OfdmModulate(t.Item1, t.Item2, t.Item3, t.Item4)),
            "ofdm_demodulate" => Bind((Complexes(a.Get("samples")), a.I("nfft"), a.I("cp_len"), a.Has("subcarriers") ? Ints(a.Get("subcarriers")) : null),
                t => Modulation.OfdmDemodulate(t.Item1, t.Item2, t.Item3, t.Item4)),
            "fsk_modulate" => Bind((Bits(a.Get("bits")), a.I("order"), a.I("samples_per_symbol"), a.D("modulation_index")),
                t => Modulation.FskModulate(t.Item1, t.Item2, t.Item3, t.Item4)),
            "fsk_demod_noncoherent" => Bind((Complexes(a.Get("samples")), a.I("order"), a.I("samples_per_symbol"), a.D("modulation_index")),
                t => Modulation.FskDemodNoncoherent(t.Item1, t.Item2, t.Item3, t.Item4)),
            "bit_errors" => Bind((Bits(a.Get("reference")), Bits(a.Get("received"))), t => Metrics.BitErrors(t.Item1, t.Item2)),
            "fft" => a.Get("samples") is Complex[] fc
                ? () => Spectral.Fft(fc)
                : Bind(Reals(a.Get("samples")), x => Spectral.Fft(x)),
            "ifft" => Bind(Complexes(a.Get("spectrum")), x => Spectral.Ifft(x)),
            "fft_frequencies" => Bind((a.I("n"), a.D("sample_rate"), a.Flag("shifted")),
                t => Spectral.FftFrequencies(t.Item1, t.Item2, t.Item3)),
            "window" => Bind((WindowName(a.Get("name")), a.I("n"), a.Flag("symmetric"), a.OptD("beta")),
                t => Spectral.Window(t.Item1, t.Item2, t.Item3, t.Item4)),
            "window_stats" => Bind(Reals(a.Get("w")), w => Spectral.WindowStats(w)),
            "welch_psd" => Welch(a),
            "coherence" => CoherenceOp(a),
            "transfer_function" => TransferFunctionOp(a),
            "coherent_output_power" => CoherenceOp(a, cop: true),
            "welch_dof" => Bind((a.I("nperseg"), a.I("noverlap"), a.I("num_segments"),
                    a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann, a.OptD("beta")),
                t => Spectral.WelchDof(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "psd_confidence_interval" => Bind((Reals(a.Get("psd")), a.D("dof"),
                    a.Has("confidence") ? a.D("confidence") : 0.95),
                t => Spectral.PsdConfidenceInterval(t.Item1, t.Item2, t.Item3)),
            "coherence_confidence_interval" => Bind((Reals(a.Get("coherence")), a.I("num_segments"),
                    a.Has("confidence") ? a.D("confidence") : 0.95),
                t => Spectral.CoherenceConfidenceInterval(t.Item1, t.Item2, t.Item3)),
            "coherence_threshold" => Bind((a.I("num_segments"), a.Has("alpha") ? a.D("alpha") : 0.05),
                t => Spectral.CoherenceThreshold(t.Item1, t.Item2)),
            "transfer_function_h2" => TransferFunctionOp(a, h2: true),
            "cross_spectral_density" => CsdOp(a),
            "dpss_tapers" => Bind((a.I("length"), a.D("half_bandwidth"), a.OptInt("num_tapers")), t => Spectral.DpssTapers(t.Item1, t.Item2, t.Item3)),
            "multitaper_psd" => MultitaperOp(a),
            "yule_walker_psd" => YuleWalkerOp(a),
            "burg_psd" => YuleWalkerOp(a, burg: true),
            "ar_psd" => ArPsdOp(a),
            "sliding_dft" => a.Get("samples") is Complex[] sds
                ? Bind((sds, a.I("length"), a.I("k")), t => Spectral.SlidingDft(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("samples")), a.I("length"), a.I("k")), t => Spectral.SlidingDft(t.Item1, t.Item2, t.Item3)),
            "goertzel" => a.Get("samples") is Complex[] gzs
                ? Bind((gzs, a.D("sample_rate"), Reals(a.Get("frequencies"))), t => Spectral.Goertzel(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("samples")), a.D("sample_rate"), Reals(a.Get("frequencies"))),
                    t => Spectral.Goertzel(t.Item1, t.Item2, t.Item3)),
            "harmonic_f_test" => FTestOp(a),
            "multitaper_line_removal" => LineRemovalOp(a),
            "spectrogram" => SpectrogramOp(a),
            "lomb_scargle_false_alarm" => Bind((a.D("power"), a.I("num_samples"), a.Has("num_frequencies") ? a.I("num_frequencies") : 1, a.Flag("center", true)),
                t => Spectral.LombScargleFalseAlarm(t.Item1, t.Item2, t.Item3, t.Item4)),
            "lomb_scargle_false_alarm_level" => Bind((a.D("probability"), a.I("num_samples"), a.Has("num_frequencies") ? a.I("num_frequencies") : 1, a.Flag("center", true)),
                t => Spectral.LombScargleFalseAlarmLevel(t.Item1, t.Item2, t.Item3, t.Item4)),
            "lomb_scargle_false_alarm_baluev" => Bind((a.D("power"), Reals(a.Get("times")), a.D("max_frequency"), a.Flag("center", true)),
                t => Spectral.LombScargleFalseAlarmBaluev(t.Item1, t.Item2, t.Item3, t.Item4)),
            "lomb_scargle_bootstrap" => Bind((Reals(a.Get("times")), Reals(a.Get("values")), Reals(a.Get("frequencies")), a.I("draws"), a.I("seed"), a.Flag("center", true)),
                t => Spectral.LombScargleBootstrap(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "lomb_scargle_false_alarm_level_baluev" => Bind((a.D("probability"), Reals(a.Get("times")), a.D("max_frequency"), a.Flag("center", true)),
                t => Spectral.LombScargleFalseAlarmLevelBaluev(t.Item1, t.Item2, t.Item3, t.Item4)),
            "lomb_scargle_frequencies" => Bind((Reals(a.Get("times")), a.Opt("oversampling", 5.0), a.OptD("max_frequency")),
                t => Spectral.LombScargleFrequencies(t.Item1, t.Item2, t.Item3)),
            "lomb_scargle" => Bind((Reals(a.Get("times")), Reals(a.Get("values")), Reals(a.Get("frequencies")), a.Flag("center", true),
                a.Has("normalization") ? Str(a, "normalization") switch
                {
                    "standard" => LombScargleNormalization.Standard,
                    "power" => LombScargleNormalization.Power,
                    _ => (LombScargleNormalization)(-1), // the library rejects it, as Python does
                } : LombScargleNormalization.Standard),
                t => Spectral.LombScargle(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "generalized_lomb_scargle" => Bind((Reals(a.Get("times")), Reals(a.Get("values")), Reals(a.Get("frequencies")),
                a.Has("uncertainties") && a.Get("uncertainties") is not null ? Reals(a.Get("uncertainties")) : null,
                a.Has("normalization") ? Str(a, "normalization") switch
                {
                    "standard" => LombScargleNormalization.Standard,
                    "power" => LombScargleNormalization.Power,
                    _ => (LombScargleNormalization)(-1), // the library rejects it, as Python does
                } : LombScargleNormalization.Standard),
                t => Spectral.GeneralizedLombScargle(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "lomb_scargle_multiterm" => Bind((Reals(a.Get("times")), Reals(a.Get("values")), Reals(a.Get("frequencies")), a.I("terms"),
                a.Has("uncertainties") && a.Get("uncertainties") is not null ? Reals(a.Get("uncertainties")) : null,
                a.Has("normalization") ? Str(a, "normalization") switch
                {
                    "standard" => LombScargleNormalization.Standard,
                    "power" => LombScargleNormalization.Power,
                    _ => (LombScargleNormalization)(-1), // the library rejects it, as Python does
                } : LombScargleNormalization.Standard),
                t => Spectral.LombScargleMultiterm(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "occupied_bandwidth" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Opt("fraction", 0.99), Span(a)),
                t => Spectral.OccupiedBandwidth(t.Item1, t.Item2, t.Item3, t.Item4)),
            "channel_power" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("low"), a.D("high"), Span(a)),
                t => Spectral.ChannelPower(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "acpr" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("center"), a.D("bandwidth"), Reals(a.Get("offsets")), a.OptD("adjacent_bandwidth"), Span(a)),
                t => Spectral.Acpr(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "spectral_decrease" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralDecrease(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_entropy" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralEntropy(t.Item1, t.Item2, t.Item3, t.Item4)),
            "harmonic_to_noise" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("fundamental"), a.D("half_width")),
                t => Spectral.HarmonicToNoise(t.Item1, t.Item2, t.Item3, t.Item4)),
            "band_energy_ratio" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("split"), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.BandEnergyRatio(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "spectral_contrast" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a), a.Opt("fraction", 0.2)),
                t => Spectral.SpectralContrast(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "spectral_crest" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralCrest(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_variation" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("previous")), Reals(a.Get("current")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralVariation(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "minimum_phase" => Bind((Reals(a.Get("samples")), a.Has("nfft") ? a.I("nfft") : (int?)null),
                t => Spectral.MinimumPhase(t.Item1, t.Item2)),
            "mel_filterbank" => Bind((a.I("n_filters"), a.I("nfft"), a.D("sample_rate"), a.OptD("min_frequency") ?? 0, a.OptD("max_frequency"), Mel(a), a.Flag("area_normalized")),
                t => Spectral.MelFilterbank(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "dct" => Bind((Reals(a.Get("samples")), a.Flag("orthonormal", true)), t => Spectral.Dct(t.Item1, t.Item2)),
            "idct" => Bind((Reals(a.Get("coefficients")), a.Flag("orthonormal", true)), t => Spectral.Idct(t.Item1, t.Item2)),
            "mfcc" => Bind((Reals(a.Get("power_spectrum")), Rows(a.Get("filterbank")), a.I("n_coefficients"), a.OptD("floor") ?? 1e-10),
                t => Spectral.Mfcc(t.Item1, t.Item2, t.Item3, t.Item4)),
            "delta" => Bind((Rows(a.Get("frames")), a.OptInt("width") ?? 2), t => Spectral.Delta(t.Item1, t.Item2)),
            "instantaneous_frequency" => Bind((Reals(a.Get("samples")), a.D("sample_rate")), t => Spectral.InstantaneousFrequency(t.Item1, t.Item2)),
            "analytic_signal" => Bind(Reals(a.Get("samples")), x => Spectral.AnalyticSignal(x)),
            "cepstral_lifter" => Bind((Reals(a.Get("coefficients")), a.OptInt("length") ?? 22), t => Spectral.CepstralLifter(t.Item1, t.Item2)),
            "real_cepstrum" => Bind((Reals(a.Get("samples")), a.Has("nfft") ? a.I("nfft") : (int?)null),
                t => Spectral.RealCepstrum(t.Item1, t.Item2)),
            "harmonic_centroid" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("heights")), Ints(a.Get("orders"))),
                t => Spectral.HarmonicCentroid(t.Item1, t.Item2, t.Item3)),
            "harmonic_deviation" => Bind((Reals(a.Get("heights")), Ints(a.Get("orders"))),
                t => Spectral.HarmonicDeviation(t.Item1, t.Item2)),
            "tristimulus" => Bind((Reals(a.Get("heights")), Ints(a.Get("orders"))),
                t => Spectral.Tristimulus(t.Item1, t.Item2)),
            "odd_even_ratio" => Bind((Reals(a.Get("heights")), Ints(a.Get("orders"))),
                t => Spectral.OddEvenRatio(t.Item1, t.Item2)),
            "inharmonicity" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("heights")), a.D("fundamental"), Ints(a.Get("orders"))),
                t => Spectral.Inharmonicity(t.Item1, t.Item2, t.Item3, t.Item4)),
            "harmonic_series" => Bind((Reals(a.Get("frequencies")), a.D("tolerance"), a.Has("max_order") ? a.I("max_order") : 10),
                t => Spectral.HarmonicSeries(t.Item1, t.Item2, t.Item3)),
            "peak_widths" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Opt("rel_height", 0.5), a.Opt("min_prominence", 0)),
                t => Spectral.PeakWidths(t.Item1, t.Item2, t.Item3, t.Item4).Select(p => (object?)p).ToList()),
            "find_tones" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.I("count"), a.Opt("min_prominence", 0),
                    !a.Has("scale") ? PeakScale.Decibel : Str(a, "scale") switch
                    {
                        "db" => PeakScale.Decibel,
                        "linear" => PeakScale.Linear,
                        _ => (PeakScale)(-1), // the library rejects it, as Python does
                    }),
                t => Spectral.FindTones(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5).Select(p => (object?)p).ToList()),
            "interpolate_peak" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.I("index"),
                    !a.Has("scale") ? PeakScale.Decibel : Str(a, "scale") switch
                    {
                        "db" => PeakScale.Decibel,
                        "linear" => PeakScale.Linear,
                        _ => (PeakScale)(-1), // the library rejects it, as Python does
                    }),
                t => Spectral.InterpolatePeak(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_peaks" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Opt("min_prominence", 0)),
                t => Spectral.SpectralPeaks(t.Item1, t.Item2, t.Item3).Select(p => (object?)p).ToList()),
            "spectral_irregularity" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralIrregularity(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_flux" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("previous")), Reals(a.Get("current")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a), a.Flag("normalize", true), a.Flag("rectify", true)),
                t => Spectral.SpectralFlux(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "spectral_flatness" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralFlatness(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_moments" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralMoments(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_rolloff" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("fraction"), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralRolloff(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "spectral_shape" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a)),
                t => Spectral.SpectralShape(t.Item1, t.Item2, t.Item3, t.Item4)),
            "spectral_slope" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Has("band") ? Pair(Reals(a.Get("band"))) : null, Span(a), a.Flag("db")),
                t => Spectral.SpectralSlope(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "db_bandwidth" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("drop_db"), a.Has("band") ? Pair(Reals(a.Get("band"))) : null),
                t => Spectral.DbBandwidth(t.Item1, t.Item2, t.Item3, t.Item4)),
            "noise_power_ratio" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), Pair(Reals(a.Get("band")))!.Value, Pair(Reals(a.Get("notch")))!.Value, Span(a)),
                t => Spectral.NoisePowerRatio(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "acpr_rrc" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("center"), a.D("symbol_rate"), a.D("alpha"), Reals(a.Get("offsets")), Span(a)),
                t => Spectral.AcprRrc(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "convolve" => Convolve(a),
            "autocorrelation" => Autocorrelation(a),
            "cross_correlation" => a.Get("x") is Complex[] || a.Get("y") is Complex[]? Bind((Complexes(a.Get("x")), Complexes(a.Get("y"))), t => Dsp.CrossCorrelation(t.Item1, t.Item2))
                : Bind((Reals(a.Get("x")), Reals(a.Get("y"))), t => Dsp.CrossCorrelation(t.Item1, t.Item2)),
            "levinson" => a.Get("r") is Complex[]? Bind((Complexes(a.Get("r")), a.I("order")), t => Dsp.Levinson(t.Item1, t.Item2))
                : Bind((Reals(a.Get("r")), a.I("order")), t => Dsp.Levinson(t.Item1, t.Item2)),
            "burg" => a.Get("samples") is Complex[] bs ? Bind((bs, a.I("order")), t => Dsp.Burg(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.I("order")), t => Dsp.Burg(t.Item1, t.Item2)),
            "ar_spectral_flatness" => a.Get("reflection") is Complex[] fk
                ? Bind(fk, t => Dsp.ArSpectralFlatness(t))
                : Bind(Reals(a.Get("reflection")), t => Dsp.ArSpectralFlatness(t)),
            "reflection_to_autocorrelation" => a.Get("reflection") is Complex[] ak
                ? Bind((ak, a.D("power"), a.I("lags")), t => Dsp.ReflectionToAutocorrelation(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("reflection")), a.D("power"), a.I("lags")),
                    t => Dsp.ReflectionToAutocorrelation(t.Item1, t.Item2, t.Item3)),
            "reflection_to_lar" => Bind(Reals(a.Get("reflection")), t => Dsp.ReflectionToLar(t)),
            "reflection_to_arcsine" => Bind(Reals(a.Get("reflection")), t => Dsp.ReflectionToArcsine(t)),
            "arcsine_to_reflection" => Bind(Reals(a.Get("arcsine")), t => Dsp.ArcsineToReflection(t)),
            "lar_to_reflection" => Bind(Reals(a.Get("lar")), t => Dsp.LarToReflection(t)),
            "lagrange_fir" => Bind((a.D("delay"), a.I("order")), t => Dsp.LagrangeFir(t.Item1, t.Item2)),
            "cepstrum_to_lpc" => a.Get("cepstrum") is Complex[] cep
                ? Bind((cep, a.I("order")), t => Dsp.CepstrumToLpc(t.Item1, t.Item2))
                : Bind((Reals(a.Get("cepstrum")), a.I("order")), t => Dsp.CepstrumToLpc(t.Item1, t.Item2)),
            "schur" => a.Get("r") is Complex[] scr
                ? Bind((scr, a.I("order")), t => Dsp.Schur(t.Item1, t.Item2))
                : Bind((Reals(a.Get("r")), a.I("order")), t => Dsp.Schur(t.Item1, t.Item2)),
            "lpc_to_autocorrelation" => a.Get("coefficients") is Complex[] lac
                ? Bind((lac, a.D("error"), a.I("lags")), t => Dsp.LpcToAutocorrelation(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("coefficients")), a.D("error"), a.I("lags")),
                    t => Dsp.LpcToAutocorrelation(t.Item1, t.Item2, t.Item3)),
            "bandwidth_expansion" => a.Get("coefficients") is Complex[] bwc
                ? Bind((bwc, a.D("factor")), t => Dsp.BandwidthExpansion(t.Item1, t.Item2))
                : Bind((Reals(a.Get("coefficients")), a.D("factor")), t => Dsp.BandwidthExpansion(t.Item1, t.Item2)),
            "cepstral_distance" => a.Get("reference") is Complex[] || a.Get("test") is Complex[]? Bind((Complexes(a.Get("reference")), Complexes(a.Get("test")), a.I("num_coefficients")),
                    t => Dsp.CepstralDistance(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("reference")), Reals(a.Get("test")), a.I("num_coefficients")),
                    t => Dsp.CepstralDistance(t.Item1, t.Item2, t.Item3)),
            "itakura_saito" => a.Get("reference") is Complex[] || a.Get("test") is Complex[]? Bind((Complexes(a.Get("reference")), a.D("reference_error"), Complexes(a.Get("test")), a.D("test_error")),
                    t => Dsp.ItakuraSaito(t.Item1, t.Item2, t.Item3, t.Item4))
                : Bind((Reals(a.Get("reference")), a.D("reference_error"), Reals(a.Get("test")), a.D("test_error")),
                    t => Dsp.ItakuraSaito(t.Item1, t.Item2, t.Item3, t.Item4)),
            "reflection_to_lpc" => a.Get("reflection") is Complex[] rk
                ? Bind(rk, t => Dsp.ReflectionToLpc(t))
                : Bind(Reals(a.Get("reflection")), t => Dsp.ReflectionToLpc(t)),
            "lpc_to_reflection" => a.Get("coefficients") is Complex[] lk
                ? Bind(lk, t => Dsp.LpcToReflection(t))
                : Bind(Reals(a.Get("coefficients")), t => Dsp.LpcToReflection(t)),
            "lattice_filter" => a.Get("samples") is Complex[] || a.Get("reflection") is Complex[]? Bind((Complexes(a.Get("samples")), Complexes(a.Get("reflection"))), t => Dsp.LatticeFilter(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), Reals(a.Get("reflection"))), t => Dsp.LatticeFilter(t.Item1, t.Item2)),
            "lattice_synthesis" => a.Get("excitation") is Complex[] || a.Get("reflection") is Complex[]? Bind((Complexes(a.Get("excitation")), Complexes(a.Get("reflection"))), t => Dsp.LatticeSynthesis(t.Item1, t.Item2))
                : Bind((Reals(a.Get("excitation")), Reals(a.Get("reflection"))), t => Dsp.LatticeSynthesis(t.Item1, t.Item2)),
            "lsf_to_lpc" => Bind(Reals(a.Get("frequencies")), t => Dsp.LsfToLpc(t)),
            "line_spectral_frequencies" => Bind(Reals(a.Get("coefficients")), t => Dsp.LineSpectralFrequencies(t)),
            "lpc_cepstrum" => a.Get("coefficients") is Complex[] lpc
                ? Bind((lpc, a.D("error"), a.I("num_coefficients")), t => Dsp.LpcCepstrum(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("coefficients")), a.D("error"), a.I("num_coefficients")),
                    t => Dsp.LpcCepstrum(t.Item1, t.Item2, t.Item3)),
            "ar_order_selection" => a.Get("samples") is Complex[] aos
                ? Bind((aos, a.I("max_order")), t => Dsp.ArOrderSelection(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.I("max_order")), t => Dsp.ArOrderSelection(t.Item1, t.Item2)),
            "upsample" => a.Get("x") is Complex[] ux
                ? Bind((ux, a.I("factor")), t => Dsp.Upsample(t.Item1, t.Item2))
                : Bind((Reals(a.Get("x")), a.I("factor")), t => Dsp.Upsample(t.Item1, t.Item2)),
            "rrc_taps" => Bind((a.D("beta"), a.I("samples_per_symbol"), a.I("span_symbols")),
                t => Dsp.RrcTaps(t.Item1, t.Item2, t.Item3)),
            "pulse_shape" => a.Get("symbols") is Complex[] ps
                ? Bind((ps, Reals(a.Get("taps")), a.I("samples_per_symbol")), t => Dsp.PulseShape(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("symbols")), Reals(a.Get("taps")), a.I("samples_per_symbol")),
                    t => Dsp.PulseShape(t.Item1, t.Item2, t.Item3)),
            "fir_lowpass" => Bind((a.I("num_taps"), a.D("cutoff"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirLowpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "fir_highpass" => Bind((a.I("num_taps"), a.D("cutoff"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirHighpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "fir_bandpass" => Bind((a.I("num_taps"), a.D("low"), a.D("high"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirBandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "fir_equiripple" => Bind((a.I("num_taps"), Reals(a.Get("bands")), Reals(a.Get("desired")), a.D("sample_rate"),
                    a.Has("weights") ? Reals(a.Get("weights")) : null, a.OptInt("grid_density") ?? 16,
                    a.Has("kind") ? FirKindName(a.Get("kind")) : FirKind.Filter),
                t => Dsp.FirEquiripple(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "gammatone" => Bind((a.D("center_frequency"), a.D("sample_rate"), a.I("length"), a.OptInt("order") ?? 4, a.OptD("bandwidth_factor") ?? 1.019),
                t => Dsp.Gammatone(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "fir_least_squares" => Bind((a.I("num_taps"), Reals(a.Get("bands")), Reals(a.Get("desired")), a.D("sample_rate"),
                    a.Has("weights") ? Reals(a.Get("weights")) : null,
                    a.Has("kind") ? FirKindName(a.Get("kind")) : FirKind.Filter),
                t => Dsp.FirLeastSquares(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "fir_frequency_sampling" => Bind((a.I("num_taps"), Reals(a.Get("frequencies")), Reals(a.Get("gains")),
                    a.D("sample_rate"), FirWindow(a), a.OptD("beta"), a.OptInt("num_points"),
                    a.Has("kind") ? FirKindName(a.Get("kind")) : FirKind.Filter),
                t => Dsp.FirFrequencySampling(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7, t.Item8)),
            "kaiser_parameters" => Bind((a.D("attenuation_db"), a.D("transition_width"), a.D("sample_rate")),
                t => Dsp.KaiserParameters(t.Item1, t.Item2, t.Item3)),
            "fir_response" => Bind((Reals(a.Get("taps")), Reals(a.Get("frequencies")), a.D("sample_rate")),
                t => Dsp.FirResponse(t.Item1, t.Item2, t.Item3)),
            "fir_group_delay" => Bind((Reals(a.Get("taps")), Reals(a.Get("frequencies")), a.D("sample_rate")),
                t => Dsp.FirGroupDelay(t.Item1, t.Item2, t.Item3)),
            "fir_filter" => ChunkedOp(a, Reals(a.Get("taps")), t => new FirFilter(t), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "iir_filter" => ChunkedOp(a, Rows(a.Get("sos")), c => new IirFilter(c), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "resampler" => ChunkedOp(a, (a.I("up"), a.I("down"), a.Has("taps") ? Reals(a.Get("taps")) : null),
                c => new Resampler(c.Item1, c.Item2, c.Item3), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "butterworth_lowpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.ButterworthLowpass(t.Item1, t.Item2, t.Item3)),
            "butterworth_highpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.ButterworthHighpass(t.Item1, t.Item2, t.Item3)),
            "chebyshev1_lowpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev1Lowpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev1_highpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev1Highpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev2_lowpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev2Lowpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev2_highpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev2Highpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "bessel_lowpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.BesselLowpass(t.Item1, t.Item2, t.Item3)),
            "bessel_highpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.BesselHighpass(t.Item1, t.Item2, t.Item3)),
            "allpass_first_order" => Bind((a.D("cutoff"), a.D("sample_rate")), t => Dsp.AllpassFirstOrder(t.Item1, t.Item2)),
            "a_weighting_sos" => Bind(a.D("sample_rate"), Dsp.AWeightingSos),
            "c_weighting_sos" => Bind(a.D("sample_rate"), Dsp.CWeightingSos),
            "thiran_allpass" => Bind((a.D("delay"), a.I("order")), t => Dsp.ThiranAllpass(t.Item1, t.Item2)),
            "allpass_second_order" => Bind((a.D("center"), a.D("bandwidth"), a.D("sample_rate")), t => Dsp.AllpassSecondOrder(t.Item1, t.Item2, t.Item3)),
            "bessel_bandpass" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.BesselBandpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "bessel_bandstop" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.BesselBandstop(t.Item1, t.Item2, t.Item3, t.Item4)),
            "elliptic_lowpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.EllipticLowpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "elliptic_highpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.EllipticHighpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "butterworth_bandpass" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.ButterworthBandpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "butterworth_bandstop" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.ButterworthBandstop(t.Item1, t.Item2, t.Item3, t.Item4)),
            "elliptic_bandpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.EllipticBandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "elliptic_bandstop" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.EllipticBandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "chebyshev1_bandpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev1Bandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev1_bandstop" => Bind((a.I("order"), a.D("ripple_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev1Bandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev2_bandpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev2Bandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev2_bandstop" => Bind((a.I("order"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev2Bandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "zero_phase_filter" => a.Get("samples") is Complex[] zs
                ? Bind((Rows(a.Get("sos")), zs, a.OptInt("pad")), t => Dsp.ZeroPhaseFilter(t.Item1, t.Item2, t.Item3))
                : Bind((Rows(a.Get("sos")), Reals(a.Get("samples")), a.OptInt("pad")), t => Dsp.ZeroPhaseFilter(t.Item1, t.Item2, t.Item3)),
            "sos_group_delay" => Bind((Rows(a.Get("sos")), Reals(a.Get("frequencies")), a.D("sample_rate")), t => Dsp.SosGroupDelay(t.Item1, t.Item2, t.Item3)),
            "sos_response" => Bind((Rows(a.Get("sos")), Reals(a.Get("frequencies")), a.D("sample_rate")), t => Dsp.SosResponse(t.Item1, t.Item2, t.Item3)),
            "encode_samples" => a.Get("x") is Complex[] z
                ? Bind((z, Str(a, "datatype")), t => Convert.ToHexStringLower(SignalFiles.EncodeSamples(t.Item1, t.Item2)))
                : Bind((Reals(a.Get("x")), Str(a, "datatype")), t => Convert.ToHexStringLower(SignalFiles.EncodeSamples(t.Item1, t.Item2))),
            "decode_samples" => DecodeSamplesOp(Convert.FromHexString(Str(a, "data")), Str(a, "datatype")),
            "read_sigmf" => ReadSigmfOp(Str(a, "file"), list: null),
            "read_sigmf_channels" => ReadSigmfOp(Str(a, "file"), list: "channels"),
            "read_sigmf_captures" => ReadSigmfOp(Str(a, "file"), list: "captures"),
            "write_wav" => WriteWavOp(Rows(a.Get("channels")), a.D("sample_rate"), Str(a, "sample_format"),
                a.Has("info") ? a.Get("info") : null, a.Has("cues") ? a.Get("cues") : null),
            "read_wav" => ReadWavOp(Str(a, "file")),
            "read_wav_info" => ReadWavInfoOp(Str(a, "file")),
            "read_wav_cues" => ReadWavCuesOp(Str(a, "file")),
            "write_npy" when a.Has("shape") => WriteNpy2DOp(a.Get("x"), Reals(a.Get("shape"))),
            "write_npy" => a.Get("x") is Complex[] nz
                ? WriteNpyOp(path => SignalFiles.WriteNpy(path, nz))
                : Bind(Reals(a.Get("x")), x => WriteNpyOp(path => SignalFiles.WriteNpy(path, x))()),
            "read_npy" => ReadNpyOp(Str(a, "file")),
            "read_npy_2d" => ReadNpy2DOp(Str(a, "file")),
            "write_npz" => WriteNpzOp(a.Get("arrays")),
            "read_npz" => ReadNpzOp(Str(a, "file")),
            "resample" => ResampleOp(a, a.I("up"), a.I("down")),
            "interpolate" => ResampleOp(a, a.I("factor"), 1),
            "decimate" => ResampleOp(a, 1, a.I("factor")),
            "cic_taps" => Bind((a.I("factor"), a.I("stages"), a.Has("delay") ? a.I("delay") : 1),
                t => Dsp.CicTaps(t.Item1, t.Item2, t.Item3)),
            "cic_compensator" => Bind((a.I("factor"), a.I("stages"), a.I("num_taps"), a.D("cutoff"), a.D("sample_rate"),
                a.Has("delay") ? a.I("delay") : 1), t => Dsp.CicCompensator(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "savgol_coefficients" => Bind((a.I("length"), a.I("order"), a.Has("derivative") ? a.I("derivative") : 0,
                a.Has("position") ? a.I("position") : 0), t => Dsp.SavgolCoefficients(t.Item1, t.Item2, t.Item3, t.Item4)),
            "moving_rms" => a.Get("samples") is Complex[] mrs
                ? Bind((mrs, a.I("length")), t => Dsp.MovingRms(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.I("length")), t => Dsp.MovingRms(t.Item1, t.Item2)),
            "envelope_follower" => a.Get("samples") is Complex[] envs
                ? Bind((envs, a.D("attack"), a.D("release")), t => Dsp.EnvelopeFollower(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("samples")), a.D("attack"), a.D("release")), t => Dsp.EnvelopeFollower(t.Item1, t.Item2, t.Item3)),
            "comb_filter" => a.Get("samples") is Complex[] cmbs
                ? Bind((cmbs, a.I("delay"), a.D("gain"), a.Flag("feedback", false)),
                    t => Dsp.CombFilter(t.Item1, t.Item2, t.Item3, t.Item4))
                : Bind((Reals(a.Get("samples")), a.I("delay"), a.D("gain"), a.Flag("feedback", false)),
                    t => Dsp.CombFilter(t.Item1, t.Item2, t.Item3, t.Item4)),
            "dc_blocker" => a.Get("samples") is Complex[] dcbs
                ? Bind((dcbs, a.D("pole")), t => Dsp.DcBlocker(t.Item1, t.Item2))
                : Bind((Reals(a.Get("samples")), a.D("pole")), t => Dsp.DcBlocker(t.Item1, t.Item2)),
            "hampel_filter" => Bind((Reals(a.Get("samples")), a.I("length"), a.Has("threshold") ? a.D("threshold") : 3.0),
                t => Dsp.HampelFilter(t.Item1, t.Item2, t.Item3)),
            "median_filter" => Bind((Reals(a.Get("samples")), a.I("length")), t => Dsp.MedianFilter(t.Item1, t.Item2)),
            "savgol_filter" => Bind((Reals(a.Get("samples")), a.I("length"), a.I("order"), a.Has("derivative") ? a.I("derivative") : 0),
                t => Dsp.SavgolFilter(t.Item1, t.Item2, t.Item3, t.Item4)),
            "cic_interpolate" => a.Get("samples") is Complex[] cici
                ? Bind((cici, a.I("factor"), a.I("stages"), a.Has("delay") ? a.I("delay") : 1),
                    t => Dsp.CicInterpolate(t.Item1, t.Item2, t.Item3, t.Item4))
                : Bind((Reals(a.Get("samples")), a.I("factor"), a.I("stages"), a.Has("delay") ? a.I("delay") : 1),
                    t => Dsp.CicInterpolate(t.Item1, t.Item2, t.Item3, t.Item4)),
            "cic_decimate" => a.Get("samples") is Complex[] cics
                ? Bind((cics, a.I("factor"), a.I("stages"), a.Has("delay") ? a.I("delay") : 1),
                    t => Dsp.CicDecimate(t.Item1, t.Item2, t.Item3, t.Item4))
                : Bind((Reals(a.Get("samples")), a.I("factor"), a.I("stages"), a.Has("delay") ? a.I("delay") : 1),
                    t => Dsp.CicDecimate(t.Item1, t.Item2, t.Item3, t.Item4)),
            "resample_taps" => Bind((a.I("up"), a.I("down")), t => Dsp.ResampleTaps(t.Item1, t.Item2)),
            "frequency_offset" => Bind((Complexes(a.Get("samples")), a.D("offset_hz"), a.D("sample_rate"), a.Opt("phase", 0)),
                t => Channel.FrequencyOffset(t.Item1, t.Item2, t.Item3, t.Item4)),
            "iq_imbalance" => Bind((Complexes(a.Get("samples")), a.D("gain_db"), a.D("phase")), t => Channel.IqImbalance(t.Item1, t.Item2, t.Item3)),
            "iq_image_rejection_db" => Bind((a.D("gain_db"), a.D("phase")), t => Channel.IqImageRejectionDb(t.Item1, t.Item2)),
            "phase_noise" => Bind((Complexes(a.Get("samples")), a.D("linewidth_hz"), a.D("sample_rate"), a.I("seed")), t => Channel.PhaseNoise(t.Item1, t.Item2, t.Item3, t.Item4)),
            "multipath" => Bind((Complexes(a.Get("samples")), Ints(a.Get("delays")), Complexes(a.Get("gains"))), t => Channel.Multipath(t.Item1, t.Item2, t.Item3)),
            "gardner_timing" => Bind((Complexes(a.Get("samples")), a.I("samples_per_symbol"), a.D("kp"), a.D("ki"), a.Opt("start", 0), a.Has("half_width") ? a.I("half_width") : 8), t => Sync.GardnerTiming(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "qpsk_carrier_tracking" => Bind((Complexes(a.Get("symbols")), a.D("kp"), a.D("ki"), a.Opt("phase", 0)), t => Sync.QpskCarrierTracking(t.Item1, t.Item2, t.Item3, t.Item4)),
            "lms_equalizer" => Bind((Complexes(a.Get("samples")), Complexes(a.Get("training")), a.I("num_taps"), a.D("step"), a.Has("samples_per_symbol") ? a.I("samples_per_symbol") : 1, a.OptInt("center"), a.Has("decision") ? Str(a, "decision") : null, a.Has("initial_taps") ? Complexes(a.Get("initial_taps")) : null), t => Sync.LmsEqualizer(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7, t.Rest.Item1)),
            "dfe_equalizer" => Bind((Complexes(a.Get("samples")), Complexes(a.Get("training")), a.I("num_taps"), a.I("num_feedback"), a.D("step"), a.Has("samples_per_symbol") ? a.I("samples_per_symbol") : 1, a.OptInt("center"), a.Has("decision") ? Str(a, "decision") : null, a.Has("initial_taps") ? Complexes(a.Get("initial_taps")) : null, a.Has("initial_feedback") ? Complexes(a.Get("initial_feedback")) : null, a.Has("phase_loop_gains") ? Pair(Reals(a.Get("phase_loop_gains"))) : null, a.Has("pilots") ? Complexes(a.Get("pilots")) : null, a.OptInt("pilot_interval"), a.Has("slip_window") ? a.I("slip_window") : 2, a.Has("forgetting") ? a.D("forgetting") : (double?)null, a.Opt("delta", 0.01)), t => Sync.DfeEqualizer(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7, t.Rest.Item1, t.Rest.Item2, t.Rest.Item3, t.Rest.Item4, t.Rest.Item5, t.Rest.Item6, t.Rest.Item7, t.Rest.Rest.Item1, t.Rest.Rest.Item2)),
            "rls_equalizer" => Bind((Complexes(a.Get("samples")), Complexes(a.Get("training")), a.I("num_taps"), a.D("forgetting"), a.Opt("delta", 0.01), a.Has("samples_per_symbol") ? a.I("samples_per_symbol") : 1, a.OptInt("center"), (a.Has("decision") ? Str(a, "decision") : null, a.Has("initial_taps") ? Complexes(a.Get("initial_taps")) : null)), t => Sync.RlsEqualizer(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7, t.Item8.Item1, t.Item8.Item2)),
            "cma_equalizer" => Bind((Complexes(a.Get("samples")), a.I("num_taps"), a.D("step"), a.Has("samples_per_symbol") ? a.I("samples_per_symbol") : 1, a.OptInt("center"), a.Opt("modulus", 1.0), a.Has("initial_taps") ? Complexes(a.Get("initial_taps")) : null), t => Sync.CmaEqualizer(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "dfe_least_squares" => Bind((Complexes(a.Get("samples")), Complexes(a.Get("training")), a.I("num_taps"), a.I("num_feedback"), a.Has("samples_per_symbol") ? a.I("samples_per_symbol") : 1, a.OptInt("center")), t => Sync.DfeLeastSquares(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "psk8_carrier_tracking" => Bind((Complexes(a.Get("symbols")), a.D("kp"), a.D("ki"), a.Opt("phase", 0)), t => Sync.Psk8CarrierTracking(t.Item1, t.Item2, t.Item3, t.Item4)),
            "qam16_carrier_tracking" => Bind((Complexes(a.Get("symbols")), a.D("kp"), a.D("ki"), a.Opt("phase", 0)), t => Sync.Qam16CarrierTracking(t.Item1, t.Item2, t.Item3, t.Item4)),
            "qam64_carrier_tracking" => Bind((Complexes(a.Get("symbols")), a.D("kp"), a.D("ki"), a.Opt("phase", 0)), t => Sync.Qam64CarrierTracking(t.Item1, t.Item2, t.Item3, t.Item4)),
            "pi_loop_gains" => Bind((a.D("loop_bandwidth"), a.D("damping"), a.D("detector_gain")), t => Sync.PiLoopGains(t.Item1, t.Item2, t.Item3)),
            "rician_fading" => Bind((Complexes(a.Get("samples")), a.D("k_factor"), a.I("block_length"), a.I("seed")), t => Channel.RicianFading(t.Item1, t.Item2, t.Item3, t.Item4)),
            "clock_drift" => Bind((Complexes(a.Get("samples")), a.D("ppm_start"), a.D("ppm_end"), a.Has("half_width") ? a.I("half_width") : 16), t => Channel.ClockDrift(t.Item1, t.Item2, t.Item3, t.Item4)),
            "clock_jitter" => Bind((Complexes(a.Get("samples")), a.D("rms"), a.I("seed"), a.Has("half_width") ? a.I("half_width") : 16), t => Channel.ClockJitter(t.Item1, t.Item2, t.Item3, t.Item4)),
            "clock_offset" => Bind((Complexes(a.Get("samples")), a.D("ppm"), a.Has("half_width") ? a.I("half_width") : 16), t => Channel.ClockOffset(t.Item1, t.Item2, t.Item3)),
            "farrow_delay" => Bind((Complexes(a.Get("samples")), Reals(a.Get("delays")), a.Has("order") ? a.I("order") : 3),
                t => Channel.FarrowDelay(t.Item1, t.Item2, t.Item3)),
            "farrow_resample" => Bind((Complexes(a.Get("samples")), a.D("ratio"), a.Has("order") ? a.I("order") : 3),
                t => Channel.FarrowResample(t.Item1, t.Item2, t.Item3)),
            "fractional_delay" => Bind((Complexes(a.Get("samples")), a.D("delay"), a.Has("half_width") ? a.I("half_width") : 16), t => Channel.FractionalDelay(t.Item1, t.Item2, t.Item3)),
            "saleh_amplifier" => Bind((Complexes(a.Get("samples")), a.D("alpha_a"), a.D("beta_a"), a.D("alpha_phi"), a.D("beta_phi")),
                t => Channel.SalehAmplifier(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "rapp_amplifier" => Bind((Complexes(a.Get("samples")), a.D("gain"), a.D("saturation"), a.D("smoothness")),
                t => Channel.RappAmplifier(t.Item1, t.Item2, t.Item3, t.Item4)),
            "dc_offset" => Bind((Complexes(a.Get("samples")), ComplexScalar(a.Get("offset"))), t => Channel.DcOffset(t.Item1, t.Item2)),
            "evm" => Bind((Complexes(a.Get("measured")), Complexes(a.Get("reference"))), t => Metrics.Evm(t.Item1, t.Item2)),
            "qpsk_ber_rayleigh_theory" => Bind(a.D("eb_n0_db"), Metrics.QpskBerRayleighTheory),
            "qpsk_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.QpskBerTheory),
            "qam16_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam16BerTheory),
            "qam64_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam64BerTheory),
            "qam64_ser_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam64SerTheory),
            "fsk_ber_theory" => Bind((a.D("eb_n0_db"), a.Has("order") ? a.I("order") : 2), t => Metrics.FskBerTheory(t.Item1, t.Item2)),
            "fsk_ser_theory" => Bind((a.D("eb_n0_db"), a.Has("order") ? a.I("order") : 2), t => Metrics.FskSerTheory(t.Item1, t.Item2)),
            "qam16_ser_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam16SerTheory),
            "psk8_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.Psk8BerTheory),
            "psk8_ser_theory" => Bind(a.D("eb_n0_db"), Metrics.Psk8SerTheory),
            "timing_offset" => Bind((Complexes(a.Get("samples")), a.I("samples_per_symbol")), t => Sync.TimingOffset(t.Item1, t.Item2)),
            "qpsk_frequency_offset" => Bind((Complexes(a.Get("symbols")), a.D("symbol_rate")), t => Sync.QpskFrequencyOffset(t.Item1, t.Item2)),
            "power_frequency_offset" => Bind((Complexes(a.Get("symbols")), a.D("symbol_rate"), a.I("power")), t => Sync.PowerFrequencyOffset(t.Item1, t.Item2, t.Item3)),
            "qpsk_phase_offset" => Bind(Complexes(a.Get("symbols")), s => Sync.QpskPhaseOffset(s)),
            "qpsk_block_phases" => Bind((Complexes(a.Get("symbols")), a.I("block_symbols")), t => Sync.QpskBlockPhases(t.Item1, t.Item2)),
            "psk8_phase_offset" => Bind(Complexes(a.Get("symbols")), s => Sync.Psk8PhaseOffset(s)),
            "psk8_block_phases" => Bind((Complexes(a.Get("symbols")), a.I("block_symbols")), t => Sync.Psk8BlockPhases(t.Item1, t.Item2)),
            "qpsk_link" => Bind(LinkConfig(a), Link.QpskLink),
            _ => throw new InvalidDataException($"unknown op {op}"),
        };
        a.CheckAllUsed();
        try
        {
            return call();
        }
        catch (ArgumentException e)
        {
            throw new LibraryArgumentException(e);
        }
    }

    private static Func<object?> Bind<T, TResult>(T args, Func<T, TResult> f) => () => f(args);

    private static (double, double)? Pair(double[] v) =>
        v.Length == 2 ? (v[0], v[1]) : throw new ArgumentException("must be a pair", nameof(v));

    private static QpskLinkConfig LinkConfig(Args a)
    {
        var d = new QpskLinkConfig { NumSymbols = a.I("num_symbols") };
        return d with
        {
            EbN0Db = a.OptD("eb_n0_db"),
            SymbolRate = a.Opt("symbol_rate", d.SymbolRate),
            SamplesPerSymbol = a.OptInt("samples_per_symbol") ?? d.SamplesPerSymbol,
            Rolloff = a.Opt("rolloff", d.Rolloff),
            SpanSymbols = a.OptInt("span_symbols") ?? d.SpanSymbols,
            DelaySamples = a.OptInt("delay_samples") ?? d.DelaySamples,
            FrequencyOffsetHz = a.Opt("frequency_offset_hz", d.FrequencyOffsetHz),
            Phase = a.Opt("phase", d.Phase),
            PreambleSymbols = a.OptInt("preamble_symbols") ?? d.PreambleSymbols,
            PhaseBlockSymbols = a.OptInt("phase_block_symbols") ?? d.PhaseBlockSymbols,
            PrbsOrder = a.OptInt("prbs_order") ?? d.PrbsOrder,
            Seed = a.OptInt("seed") ?? d.Seed,
        };
    }

    private static Func<object?> Tone(Args a)
    {
        var (fs, n, f, amp, ph) = (a.D("sample_rate"), a.I("num_samples"), a.D("frequency"), a.Opt("amplitude", 1), a.Opt("phase", 0));
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Tone(fs, n, f, amp, ph)
            : () => Waveforms.RealTone(fs, n, f, amp, ph);
    }

    private static Func<object?> Multitone(Args a)
    {
        var (fs, n, f) = (a.D("sample_rate"), a.I("num_samples"), Reals(a.Get("frequencies")));
        double[]? amps = a.Has("amplitudes") ? Reals(a.Get("amplitudes")) : null;
        double[]? phases = a.Has("phases") ? Reals(a.Get("phases")) : null;
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Multitone(fs, n, f, amps, phases)
            : () => Waveforms.RealMultitone(fs, n, f, amps, phases);
    }

    private static Func<object?> Chirp(Args a)
    {
        var (fs, n, f0, f1, amp, ph) = (a.D("sample_rate"), a.I("num_samples"), a.D("start"), a.D("stop"), a.Opt("amplitude", 1), a.Opt("phase", 0));
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Chirp(fs, n, f0, f1, amp, ph)
            : () => Waveforms.RealChirp(fs, n, f0, f1, amp, ph);
    }

    private static Func<object?> Prbs(Args a)
    {
        var (order, n, invert) = (a.I("order"), a.I("num_bits"), a.Flag("invert"));
        uint? seed = a.Has("seed") ? (a.I("seed") is var v and >= 0 ? (uint)v : throw new InvalidDataException("seed < 0")) : null;
        return () => Waveforms.Prbs(order, n, seed, invert);
    }

    private static Func<object?> CoherenceOp(Args a, bool cop = false)
    {
        object? xs = a.Get("x"), ys = a.Get("y");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.OptInt("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        if (xs is Complex[] || ys is Complex[])
        {
            Complex[] xc = Complexes(xs), yc = Complexes(ys);
            return cop
                ? () => Spectral.CoherentOutputPower(xc, yc, fs, nperseg, noverlap, window, beta, detrend, nfft)
                : () => Spectral.Coherence(xc, yc, fs, nperseg, noverlap, window, beta, detrend, nfft);
        }
        double[] x = Reals(xs), y = Reals(ys);
        return cop
            ? () => Spectral.CoherentOutputPower(x, y, fs, nperseg, noverlap, window, beta, detrend, nfft)
            : () => Spectral.Coherence(x, y, fs, nperseg, noverlap, window, beta, detrend, nfft);
    }

    private static Func<object?> TransferFunctionOp(Args a, bool h2 = false)
    {
        object? xs = a.Get("x"), ys = a.Get("y");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.OptInt("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        if (xs is Complex[] || ys is Complex[])
        {
            Complex[] xc = Complexes(xs), yc = Complexes(ys);
            return h2
                ? () => Spectral.TransferFunctionH2(xc, yc, fs, nperseg, noverlap, window, beta, detrend, nfft)
                : () => Spectral.TransferFunction(xc, yc, fs, nperseg, noverlap, window, beta, detrend, nfft);
        }
        double[] x = Reals(xs), y = Reals(ys);
        return h2
            ? () => Spectral.TransferFunctionH2(x, y, fs, nperseg, noverlap, window, beta, detrend, nfft)
            : () => Spectral.TransferFunction(x, y, fs, nperseg, noverlap, window, beta, detrend, nfft);
    }

    private static Func<object?> CsdOp(Args a)
    {
        object? xs = a.Get("x"), ys = a.Get("y");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.OptInt("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        if (xs is Complex[] || ys is Complex[])
        {
            // C# has no one-sided option for complex samples (Python raises for one_sided=True).
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            Complex[] xc = Complexes(xs), yc = Complexes(ys);
            return () => Spectral.CrossSpectralDensity(xc, yc, fs, nperseg, noverlap, window, beta, detrend, nfft);
        }
        double[] x = Reals(xs), y = Reals(ys);
        bool oneSided = a.Flag("one_sided", true);
        return () => Spectral.CrossSpectralDensity(x, y, fs, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
    }

    private static Func<object?> Welch(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.OptInt("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        var average = a.Has("average") ? Str(a, "average") switch
        {
            "mean" => WelchAverage.Mean,
            "median" => WelchAverage.Median,
            _ => (WelchAverage)(-1), // the library rejects it, as Python does
        } : WelchAverage.Mean;
        if (samples is Complex[] cs)
        {
            // C# has no one-sided option for complex samples (Python raises for one_sided=True).
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.WelchPsd(cs, fs, nperseg, noverlap, window, beta, detrend, average, nfft);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.WelchPsd(x, fs, nperseg, noverlap, window, oneSided, beta, detrend, average, nfft);
    }

    private static Detrend DetrendName(Args a) => a.Has("detrend") ? Str(a, "detrend") switch
    {
        "none" => Detrend.None,
        "constant" => Detrend.Constant,
        "linear" => Detrend.Linear,
        _ => (Detrend)(-1), // the library rejects it, as Python does
    } : Detrend.None;

    private static Func<object?> ToneMetricsOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate");
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width, fundamental) = (a.OptD("beta"), a.OptInt("width"), a.OptD("fundamental"));
        int harmonics = a.Has("num_harmonics") ? a.I("num_harmonics") : 5;
        if (samples is Complex[] cs)
            return () => Measurements.ToneMetrics(cs, fs, window, beta, width, harmonics, fundamental);
        double[] x = Reals(samples);
        return () => Measurements.ToneMetrics(x, fs, window, beta, width, harmonics, fundamental);
    }

    private static Func<object?> SfdrOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate");
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width, fundamental) = (a.OptD("beta"), a.OptInt("width"), a.OptD("fundamental"));
        int spurs = a.Has("num_spurs") ? a.I("num_spurs") : 1;
        if (samples is Complex[] cs)
            return () => Measurements.Sfdr(cs, fs, window, beta, width, fundamental, spurs);
        double[] x = Reals(samples);
        return () => Measurements.Sfdr(x, fs, window, beta, width, fundamental, spurs);
    }

    private static Func<object?> TwoToneImdOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, f1, f2) = (a.D("sample_rate"), a.D("f1"), a.D("f2"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width) = (a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.TwoToneImd(cs, fs, f1, f2, window, beta, width);
        double[] x = Reals(samples);
        return () => Measurements.TwoToneImd(x, fs, f1, f2, window, beta, width);
    }

    private static Func<object?> TwoToneIp2Op(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, f1, f2) = (a.D("sample_rate"), a.D("f1"), a.D("f2"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width) = (a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.TwoToneIp2(cs, fs, f1, f2, window, beta, width);
        double[] x = Reals(samples);
        return () => Measurements.TwoToneIp2(x, fs, f1, f2, window, beta, width);
    }

    private static Func<object?> TwoToneIp5Op(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, f1, f2) = (a.D("sample_rate"), a.D("f1"), a.D("f2"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width) = (a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.TwoToneIp5(cs, fs, f1, f2, window, beta, width);
        double[] x = Reals(samples);
        return () => Measurements.TwoToneIp5(x, fs, f1, f2, window, beta, width);
    }

    private static Func<object?> PhaseNoiseSsbOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate");
        double[] offsets = Reals(a.Get("offsets"));
        double[]? spurs = a.Has("spur_offsets") ? Reals(a.Get("spur_offsets")) : null;
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (carrier, nperseg, beta, width) = (a.OptD("carrier"), a.OptInt("nperseg"), a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.PhaseNoiseSsb(cs, fs, offsets, carrier, nperseg, window, beta, width, spurs);
        double[] x = Reals(samples);
        return () => Measurements.PhaseNoiseSsb(x, fs, offsets, carrier, nperseg, window, beta, width, spurs);
    }

    private static Func<object?> IntegratedPhaseNoiseOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate"), lo = a.D("f_lo"), hi = a.D("f_hi");
        double[]? spurs = a.Has("spur_offsets") ? Reals(a.Get("spur_offsets")) : null;
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (carrier, nperseg, beta, width) = (a.OptD("carrier"), a.OptInt("nperseg"), a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.IntegratedPhaseNoise(cs, fs, lo, hi, carrier, nperseg, window, beta, width, spurs);
        double[] x = Reals(samples);
        return () => Measurements.IntegratedPhaseNoise(x, fs, lo, hi, carrier, nperseg, window, beta, width, spurs);
    }

    private static Func<object?> PhaseNoiseSpursOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate"), lo = a.D("f_lo"), hi = a.D("f_hi");
        double threshold = a.OptD("threshold_db") ?? 10.0;
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (carrier, nperseg, beta, width) = (a.OptD("carrier"), a.OptInt("nperseg"), a.OptD("beta"), a.OptInt("width"));
        if (samples is Complex[] cs)
            return () => Measurements.PhaseNoiseSpurs(cs, fs, lo, hi, threshold, carrier, nperseg, window, beta, width);
        double[] x = Reals(samples);
        return () => Measurements.PhaseNoiseSpurs(x, fs, lo, hi, threshold, carrier, nperseg, window, beta, width);
    }

    private static Func<object?> FTestOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nw, k, nfft) = (a.D("sample_rate"), a.D("half_bandwidth"), a.OptInt("num_tapers"), a.OptInt("nfft"));
        if (samples is Complex[] cs)
            return () => Spectral.HarmonicFTest(cs, fs, nw, k, nfft);
        double[] x = Reals(samples);
        return () => Spectral.HarmonicFTest(x, fs, nw, k, nfft);
    }

    private static Func<object?> ArPsdOp(Args a)
    {
        object? coefficients = a.Get("coefficients");
        var (error, fs, nfft) = (a.D("error"), a.D("sample_rate"), a.I("nfft"));
        if (coefficients is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex coefficients has no C# form");
            return () => Spectral.ArPsd(cs, error, fs, nfft);
        }
        double[] x = Reals(coefficients);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.ArPsd(x, error, fs, nfft, oneSided);
    }

    private static Func<object?> YuleWalkerOp(Args a, bool burg = false)
    {
        object? samples = a.Get("samples");
        var (fs, order, nfft) = (a.D("sample_rate"), a.I("order"), a.OptInt("nfft"));
        if (samples is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => burg ? Spectral.BurgPsd(cs, fs, order, nfft) : Spectral.YuleWalkerPsd(cs, fs, order, nfft);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => burg ? Spectral.BurgPsd(x, fs, order, nfft, oneSided) : Spectral.YuleWalkerPsd(x, fs, order, nfft, oneSided);
    }

    private static Func<object?> MultitaperOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nw, k, nfft) = (a.D("sample_rate"), a.D("half_bandwidth"), a.OptInt("num_tapers"), a.OptInt("nfft"));
        bool adaptive = a.Flag("adaptive");
        if (samples is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.MultitaperPsd(cs, fs, nw, k, nfft, adaptive);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.MultitaperPsd(x, fs, nw, k, oneSided, nfft, adaptive);
    }

    private static Func<object?> LineRemovalOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nw, k, nfft) = (a.D("sample_rate"), a.D("half_bandwidth"), a.OptInt("num_tapers"), a.OptInt("nfft"));
        var (probability, adaptive) = (a.OptD("probability"), a.Flag("adaptive"));
        if (samples is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.MultitaperLineRemoval(cs, fs, nw, probability, k, nfft, adaptive);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.MultitaperLineRemoval(x, fs, nw, probability, k, oneSided, nfft, adaptive);
    }

    private static Func<object?> SpectrogramOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.I("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        if (samples is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.Spectrogram(cs, fs, nperseg, noverlap, window, beta, detrend, nfft);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.Spectrogram(x, fs, nperseg, noverlap, window, oneSided, beta, detrend, nfft);
    }

    /// <summary>Real only when both inputs are real, as in NumPy.</summary>
    private static MelScale Mel(Args a) => a.Has("scale") ? Str(a, "scale") switch
    {
        "htk" => MelScale.Htk,
        "slaney" => MelScale.Slaney,
        _ => (MelScale)(-1), // the library rejects it, as Python does
    } : MelScale.Htk;

    private static Func<object?> Autocorrelation(Args a)
    {
        object? x = a.Get("samples");
        int? maxLag = a.Has("max_lag") ? a.I("max_lag") : null;
        var scaling = a.Has("scaling") ? Str(a, "scaling") switch
        {
            "biased" => CorrelationScaling.Biased,
            "unbiased" => CorrelationScaling.Unbiased,
            "none" => CorrelationScaling.None,
            _ => (CorrelationScaling)(-1), // the library rejects it, as Python does
        } : CorrelationScaling.Biased;
        return x is Complex[]? Bind(Complexes(x), c => Dsp.Autocorrelation(c, maxLag, scaling))
            : Bind(Reals(x), r => Dsp.Autocorrelation(r, maxLag, scaling));
    }

    private static Func<object?> Convolve(Args a)
    {
        object? x = a.Get("x"), h = a.Get("h");
        if (x is Complex[] || h is Complex[])
        {
            Complex[] cx = Complexes(x);
            return h is Complex[] ch ? () => Dsp.Convolve(cx, ch) : Bind(Reals(h), rh => Dsp.Convolve(cx, rh));
        }
        return Bind((Reals(x), Reals(h)), t => Dsp.Convolve(t.Item1, t.Item2));
    }

    private static string Str(Args a, string k) => a.Get(k) as string ?? throw new InvalidDataException($"{k} must be a string");

    private static Func<object?> DecodeSamplesOp(byte[] data, string datatype) => datatype.StartsWith('c')
        ? () => SignalFiles.DecodeSamples<Complex>(data, datatype)
        : () => SignalFiles.DecodeSamples<double>(data, datatype);

    /// <summary>A recording in vectors/files, read as the kind its datatype names (the runner
    /// peeks; a file it can't peek at is read as real, and the library must reject it).</summary>
    private static Func<object?> ReadSigmfOp(string name, string? list)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        bool isComplex = false;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllBytes(path + ".sigmf-meta"));
            isComplex = doc.RootElement.GetProperty("global").GetProperty("core:datatype").GetString()?.StartsWith('c') == true;
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException)
        {
        }
        if (list is not null)
        {
            bool channels = list == "channels";
            return isComplex
                ? () => (channels ? SignalFiles.ReadSigmfChannels<Complex>(path) : SignalFiles.ReadSigmfCaptures<Complex>(path))
                    .Select(s => (object?)SignalRecord(s)).ToList()
                : () => (channels ? SignalFiles.ReadSigmfChannels<double>(path) : SignalFiles.ReadSigmfCaptures<double>(path))
                    .Select(s => (object?)SignalRecord(s)).ToList();
        }
        return isComplex
            ? () => SignalRecord(SignalFiles.ReadSigmf<Complex>(path))
            : () => SignalRecord(SignalFiles.ReadSigmf<double>(path));
    }

    private static Func<object?> WriteWavOp(double[][] rows, double rate, string format, object? info, object? cues)
    {
        // A list of {id, text} records; an empty JSON list decodes as an empty number array.
        List<KeyValuePair<string, string>>? tags = info switch
        {
            null => null,
            double[] { Length: 0 } => [],
            _ => [.. ((List<object?>)info).Cast<Dictionary<string, object?>>()
                .Select(d => new KeyValuePair<string, string>((string)d["id"]!, (string)d["text"]!))],
        };
        // {position, length, label} records, likewise.
        List<(long Position, long Length, string Label)>? marks = cues switch
        {
            null => null,
            double[] { Length: 0 } => [],
            _ => [.. ((List<object?>)cues).Cast<Dictionary<string, object?>>()
                .Select(d => (Whole((double)d["position"]!), Whole((double)d["length"]!), (string)d["label"]!))],
        };
        return WriteWavOp(rows, rate, format, tags, marks);
    }

    private static long Whole(double x) =>
        x == Math.Floor(x) && Math.Abs(x) < 1e18 ? (long)x : throw new InvalidDataException($"{x} is not a whole number");

    private static Func<object?> ReadWavCuesOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        return () => SignalFiles.ReadWavCues(path)
            .Select(c => (object?)new Dictionary<string, object?> { ["position"] = (double)c.Position, ["length"] = (double)c.Length, ["label"] = c.Label }).ToList();
    }

    private static Func<object?> ReadWavInfoOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        return () => SignalFiles.ReadWavInfo(path)
            .Select(kv => (object?)new Dictionary<string, object?> { ["id"] = kv.Key, ["text"] = kv.Value }).ToList();
    }

    private static Func<object?> WriteWavOp(double[][] rows, double rate, string format,
        List<KeyValuePair<string, string>>? tags, List<(long Position, long Length, string Label)>? cues) => () =>
    {
        string path = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".wav");
        try
        {
            SignalFiles.WriteWav(path, [.. rows.Select(r => new Signal<double>(r, rate))], format, tags, cues);
            return Convert.ToHexStringLower(File.ReadAllBytes(path));
        }
        finally
        {
            File.Delete(path);
        }
    };

    private static Func<object?> WriteNpzOp(object? arrays)
    {
        // A list of {name, x} records, {name, shape, x} for a 2-D member; an empty JSON list decodes as an empty
        // number array.
        List<KeyValuePair<string, Array>> items = arrays is double[] { Length: 0 } ? [] :
            [.. ((List<object?>)arrays!).Cast<Dictionary<string, object?>>()
                .Select(d => new KeyValuePair<string, Array>((string)d["name"]!,
                    d.TryGetValue("shape", out object? shape) ? Matrix(d["x"], Reals(shape)) : (Array)d["x"]!))];
        return WriteNpyOp(path => SignalFiles.WriteNpz(path, items));
    }

    private static Func<object?> ReadNpzOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        return () => SignalFiles.ReadNpz(path).Select(kv =>
        {
            Dictionary<string, object?> record = kv.Value switch
            {
                double[,] m => MatrixRecord(m),
                Complex[,] m => MatrixRecord(m),
                _ => new() { ["x"] = kv.Value },
            };
            record["name"] = kv.Key;
            return (object?)record;
        }).ToList();
    }

    private static Func<object?> WriteNpyOp(Action<string> write) => () =>
    {
        string path = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".npy");
        try
        {
            write(path);
            return Convert.ToHexStringLower(File.ReadAllBytes(path));
        }
        finally
        {
            File.Delete(path);
        }
    };

    private static Func<object?> WriteNpy2DOp(object? x, double[] shape) => Matrix(x, shape) switch
    {
        Complex[,] z => WriteNpyOp(path => SignalFiles.WriteNpy(path, z)),
        var m => WriteNpyOp(path => SignalFiles.WriteNpy(path, (double[,])m)),
    };

    /// <summary>A <see cref="double"/>[,] or <see cref="Complex"/>[,] from values flat in C order and a shape.</summary>
    private static Array Matrix(object? x, double[] shape)
    {
        if (shape is not [var r, var c] || r < 0 || c < 0 || r != Math.Floor(r) || c != Math.Floor(c))
            throw new InvalidDataException("shape must be two non-negative whole numbers");
        if (x is Complex[] z)
        {
            var zm = new Complex[(int)r, (int)c];
            if (z.Length != zm.Length)
                throw new InvalidDataException("x must have rows x columns values");
            for (int k = 0; k < z.Length; k++)
                zm[k / (int)c, k % (int)c] = z[k];
            return zm;
        }
        double[] v = Reals(x);
        var m = new double[(int)r, (int)c];
        if (v.Length != m.Length)
            throw new InvalidDataException("x must have rows x columns values");
        for (int k = 0; k < v.Length; k++)
            m[k / (int)c, k % (int)c] = v[k];
        return m;
    }

    private static Func<object?> ReadNpy2DOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        bool isComplex = System.Text.RegularExpressions.Regex.IsMatch(File.ReadAllText(path, System.Text.Encoding.Latin1), "[<>]c(16|8)['\"]");
        return isComplex ? () => MatrixRecord(SignalFiles.ReadNpy2D<Complex>(path)) : () => MatrixRecord(SignalFiles.ReadNpy2D<double>(path));
    }

    /// <summary>A 2-D array as its shape and its values flat in C order.</summary>
    private static Dictionary<string, object?> MatrixRecord<T>(T[,] m) => new()
    {
        ["shape"] = new double[] { m.GetLength(0), m.GetLength(1) },
        ["x"] = m.Cast<T>().ToArray(),
    };

    private static Func<object?> ReadNpyOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        // The runner picks the element type from the descr, as ReadSigmfOp does from the metadata.
        bool isComplex = System.Text.RegularExpressions.Regex.IsMatch(File.ReadAllText(path, System.Text.Encoding.Latin1), "[<>]c(16|8)['\"]");
        return isComplex ? () => SignalFiles.ReadNpy<Complex>(path) : () => SignalFiles.ReadNpy<double>(path);
    }

    private static Func<object?> ReadWavOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        return () =>
        {
            Signal<double>[] s = SignalFiles.ReadWav(path);
            return new Dictionary<string, object?>
            {
                ["channels"] = s.Select(c => c.Samples.ToArray()).ToArray(),
                ["sample_rate"] = s[0].SampleRate,
                ["units"] = s[0].Units,
            };
        };
    }

    private static Dictionary<string, object?> SignalRecord<T>(Signal<T> s) where T : struct => new()
    {
        ["samples"] = s.Samples.ToArray(),
        ["sample_rate"] = s.SampleRate,
        ["center_frequency"] = s.CenterFrequency,
        ["time_origin"] = s.TimeOrigin,
        ["units"] = s.Units,
        ["impedance"] = s.Impedance,
        ["metadata"] = s.Metadata.ToDictionary(kv => kv.Key, kv => kv.Value),
    };

    private static Func<object?> ResampleOp(Args a, int up, int down)
    {
        object? x = a.Get("x");
        double[]? taps = a.Has("taps") ? Reals(a.Get("taps")) : null;
        return x is Complex[] z
            ? () => Dsp.Resample(z, up, down, taps)
            : Bind(Reals(x), r => Dsp.Resample(r, up, down, taps));
    }

    private static WindowType FirWindow(Args a) => a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hamming;

    /// <summary>A 2-D vector argument as rows.</summary>
    private static double[][] Rows(object? v) =>
        v switch
        {
            double[][] rows => rows,
            Array { Length: 0 } => [],
            _ => throw new InvalidDataException("expected an array of rows"),
        };

    /// <summary>Runs the samples through one streaming filter, made from the coefficients when the
    /// case runs, in chunks of the given lengths.</summary>
    private static Func<object?> ChunkedOp<TCoefficients, TFilter>(Args a, TCoefficients coefficients, Func<TCoefficients, TFilter> make,
        Func<TFilter, double[], double[]> real, Func<TFilter, Complex[], Complex[]> complex)
    {
        object? samples = a.Get("samples");
        int[] sizes = [.. Reals(a.Get("chunks")).Select(c => c >= 0 && c == Math.Floor(c) && c <= int.MaxValue
            ? (int)c : throw new InvalidDataException("chunks must be non-negative whole numbers"))];
        int total = samples is Complex[] zc ? zc.Length : Reals(samples).Length;
        if (sizes.Sum() != total)
            throw new InvalidDataException("chunks must add up to the number of samples");
        return () =>
        {
            TFilter f = make(coefficients);
            int at = 0;
            if (samples is Complex[] z)
            {
                var yz = new List<Complex>();
                foreach (int c in sizes)
                {
                    yz.AddRange(complex(f, z[at..(at + c)]));
                    at += c;
                }
                return yz.ToArray();
            }
            double[] x = Reals(samples);
            var y = new List<double>();
            foreach (int c in sizes)
            {
                y.AddRange(real(f, x[at..(at + c)]));
                at += c;
            }
            return y.ToArray();
        };
    }

    private static (double Low, double High)? Span(Args a)
    {
        if (!a.Has("span"))
            return null;
        double[] s = Reals(a.Get("span"));
        return s.Length == 2 ? (s[0], s[1]) : throw new InvalidDataException("span must have two values");
    }

    /// <summary>Vector window names: exactly the Python names. An unknown name is a library error in
    /// Python, so it maps to an undefined enum value that the library must reject.</summary>
    private static WindowType WindowName(object? v) => (v as string) switch
    {
        "rectangular" => WindowType.Rectangular,
        "hann" => WindowType.Hann,
        "hamming" => WindowType.Hamming,
        "blackman" => WindowType.Blackman,
        "blackman_harris" => WindowType.BlackmanHarris,
        "flattop" => WindowType.Flattop,
        "kaiser" => WindowType.Kaiser,
        string => (WindowType)(-1),
        _ => throw new InvalidDataException("window name must be a string"),
    };

    /// <summary>Vector equiripple kinds: the Python names; an unknown one maps to an undefined
    /// value the library must reject.</summary>
    private static FirKind FirKindName(object? v) => (v as string) switch
    {
        "filter" => FirKind.Filter,
        "hilbert" => FirKind.Hilbert,
        "differentiator" => FirKind.Differentiator,
        string => (FirKind)(-1),
        _ => throw new InvalidDataException("kind must be a string"),
    };

    private static double[] Reals(object? v) => v as double[] ?? throw new InvalidDataException("expected a real array");

    private static int[] Ints(object? v) => Reals(v).Select(x =>
        x >= int.MinValue && x <= int.MaxValue && x == Math.Floor(x)
            ? (int)x
            : throw new InvalidDataException($"not representable as an int: {x}")).ToArray();

    private static Complex ComplexScalar(object? v) => v switch
    {
        Complex c => c,
        double d => new Complex(d, 0),
        _ => throw new InvalidDataException("expected a number"),
    };

    private static Complex[] Complexes(object? v) =>
        v as Complex[] ?? Reals(v).Select(x => new Complex(x, 0)).ToArray();

    /// <summary>Bits as bytes. A value that is not 0 or 1 has no byte form the library could reject
    /// for being a non-bit (e.g. 0.5), so it is a bad case, except whole numbers 2…255, which the
    /// library must reject.</summary>
    private static byte[] Bits(object? v) => Reals(v).Select(x =>
        x is >= 0 and <= byte.MaxValue && x == Math.Floor(x)
            ? (byte)x
            : throw new InvalidDataException($"not representable as a byte: {x}")).ToArray();

    /// <summary>JSON vector value to: double, bool, string, double[], Complex, Complex[], or a record dictionary.</summary>
    public static object? Decode(JsonElement v)
    {
        switch (v.ValueKind)
        {
            case JsonValueKind.Null:
                return null;
            case JsonValueKind.Number:
                return v.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.String:
                return v.GetString() switch
                {
                    "inf" => double.PositiveInfinity,
                    "-inf" => double.NegativeInfinity,
                    "nan" => double.NaN,
                    var s => s,
                };
            case JsonValueKind.Array:
                if (v.EnumerateArray().Any(IsItem)) // a list of records or strings, not an array
                    return v.EnumerateArray().Select(Decode).ToList();
                if (v.GetArrayLength() > 0 && v[0].ValueKind == JsonValueKind.Array)
                    return v.EnumerateArray().Select(e => (double[])Decode(e)!).ToArray(); // rows of a 2-D result
                return v.EnumerateArray().Select(e => (double)Decode(e)!).ToArray();
            case JsonValueKind.Object:
                var props = v.EnumerateObject().ToList();
                if (props.Count == 2 && v.TryGetProperty("re", out var re) && v.TryGetProperty("im", out var im))
                {
                    if (re.ValueKind == JsonValueKind.Array)
                    {
                        var r = (double[])Decode(re)!;
                        var i = (double[])Decode(im)!;
                        if (r.Length != i.Length)
                            throw new InvalidDataException("re and im have different lengths");
                        return r.Zip(i, (x, y) => new Complex(x, y)).ToArray();
                    }
                    return new Complex((double)Decode(re)!, (double)Decode(im)!);
                }
                return props.ToDictionary(p => p.Name, p => Decode(p.Value));
            default:
                return null;
        }
    }

    /// <summary>Whether <paramref name="x"/> makes the JSON array holding it a list rather than a number array.</summary>
    private static bool IsItem(JsonElement x) => x.ValueKind switch
    {
        JsonValueKind.String => x.GetString() is not ("inf" or "-inf" or "nan"),
        JsonValueKind.Object => !(x.EnumerateObject().Count() == 2 && x.TryGetProperty("re", out _) && x.TryGetProperty("im", out _)),
        JsonValueKind.Null or JsonValueKind.True or JsonValueKind.False => true,
        _ => false,
    };

    /// <summary>Result to the decoded-vector shape: numbers as double, arrays as double[]/Complex[], records as snake_case dictionaries.</summary>
    public static object? Canonical(object? v) => v switch
    {
        null => null,
        double or Complex or Complex[] or double[] or double[][] or bool or string => v,
        long l => (double)l,
        Dictionary<string, object?> m => m.ToDictionary(kv => kv.Key, kv => Canonical(kv.Value)),
        List<object?> l when l.All(x => x is long or double) => l.Select(x => Convert.ToDouble(x, CultureInfo.InvariantCulture)).ToArray(),
        List<object?> l => l.Select(Canonical).ToList(),
        int i => (double)i,
        byte[] b => b.Select(x => (double)x).ToArray(),
        int[] ia => ia.Select(x => (double)x).ToArray(),
        System.Runtime.CompilerServices.ITuple t => Enumerable.Range(0, t.Length).Select(i => Convert.ToDouble(t[i], CultureInfo.InvariantCulture)).ToArray(),
        _ when v.GetType().Assembly == typeof(Units).Assembly =>
            v.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .ToDictionary(p => SnakeCase(p.Name), p => Canonical(p.GetValue(v))),
        _ => throw new InvalidOperationException($"no canonical form for {v.GetType()}"),
    };

    public static string SnakeCase(string name)
    {
        var sb = new StringBuilder();
        for (int i = 0; i < name.Length; i++)
        {
            if (char.IsUpper(name[i]) && i > 0)
                sb.Append('_');
            sb.Append(char.ToLowerInvariant(name[i]));
        }
        return sb.ToString();
    }

    private static void Compare(object? actual, object? expected, double abs, double rel, string path, List<string> msgs)
    {
        string where = path.Length == 0 ? "value" : path;
        switch (expected)
        {
            case null:
                if (actual is not null) msgs.Add($"{where}: expected null, got {actual.GetType().Name}");
                return;
            case Dictionary<string, object?> rec:
                if (actual is not Dictionary<string, object?> act)
                {
                    msgs.Add($"{where}: expected a record, got {actual?.GetType().Name ?? "null"}");
                    return;
                }
                foreach (var (k, e) in rec)
                {
                    string p = path.Length == 0 ? k : $"{path}.{k}";
                    if (act.TryGetValue(k, out var x)) Compare(x, e, abs, rel, p, msgs);
                    else msgs.Add($"{p}: missing");
                }
                return;
            case double[] ed when actual is double[] ad:
                if (ad.Length != ed.Length)
                    msgs.Add($"{where}: length {ad.Length} != expected {ed.Length}");
                else if (Enumerable.Range(0, ed.Length).Where(i => !Close(ad[i], ed[i], abs, rel)).ToList() is [int i0, ..] bad)
                    msgs.Add($"{where}[{i0}]: {ad[i0]:R} != expected {ed[i0]:R} ({bad.Count} differ)");
                return;
            case double[][] er when actual is double[][] ar:
                if (ar.Length != er.Length)
                    msgs.Add($"{where}: {ar.Length} rows != expected {er.Length}");
                else
                    for (int r = 0; r < er.Length; r++)
                        Compare(ar[r], er[r], abs, rel, $"{where}[{r}]", msgs);
                return;
            case Complex[] ec when actual is Complex[] ac:
                CompareArrays(ac, ec, abs, rel, where, msgs);
                return;
            case List<object?> el:
                if (actual is not List<object?> al)
                    msgs.Add($"{where}: expected a list, got {actual?.GetType().Name ?? "null"}");
                else if (al.Count != el.Count)
                    msgs.Add($"{where}: length {al.Count} != expected {el.Count}");
                else
                    for (int i = 0; i < el.Count; i++)
                        Compare(al[i], el[i], abs, rel, $"{where}[{i}]", msgs);
                return;
            case string es:
                if (actual as string != es) msgs.Add($"{where}: {actual ?? "null"} != expected {es}");
                return;
            case bool eb when actual is bool ab:
                if (ab != eb) msgs.Add($"{where}: {ab} != expected {eb}");
                return;
            case double ed when actual is double ad:
                if (!Close(ad, ed, abs, rel)) msgs.Add($"{where}: {ad:R} != expected {ed:R}");
                return;
            case Complex ec when actual is Complex ac:
                if (!Close(ac, ec, abs, rel)) msgs.Add($"{where}: {ac} != expected {ec}");
                return;
            default:
                msgs.Add($"{where}: type {actual?.GetType().Name ?? "null"} does not match expected {expected?.GetType().Name ?? "null"}");
                return;
        }
    }

    private static void CompareArrays(Complex[] a, Complex[] e, double abs, double rel, string where, List<string> msgs)
    {
        if (a.Length != e.Length)
        {
            msgs.Add($"{where}: length {a.Length} != expected {e.Length}");
            return;
        }
        var bad = Enumerable.Range(0, e.Length).Where(i => !Close(a[i], e[i], abs, rel)).ToList();
        if (bad.Count > 0)
            msgs.Add($"{where}[{bad[0]}]: {a[bad[0]]} != expected {e[bad[0]]} ({bad.Count} differ)");
    }

    private static bool Close(double a, double e, double abs, double rel)
    {
        if (double.IsNaN(e)) return double.IsNaN(a);
        if (double.IsInfinity(e)) return a == e;
        return Math.Abs(a - e) <= abs + rel * Math.Abs(e);
    }

    private static bool Close(Complex a, Complex e, double abs, double rel) =>
        double.IsFinite(e.Real) && double.IsFinite(e.Imaginary)
            ? Complex.Abs(a - e) <= abs + rel * Complex.Abs(e)
            : Close(a.Real, e.Real, abs, rel) && Close(a.Imaginary, e.Imaginary, abs, rel); // part by part, so inf matches inf
}
