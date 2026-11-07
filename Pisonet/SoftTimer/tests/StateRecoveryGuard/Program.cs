// Source-linked paid-session recovery regression. Uses disposable temp files only.
using System.Text.Json;
using BlazePisonet.SoftTimer;

static void Require(bool good, string message)
{
    if (!good) throw new InvalidOperationException(message);
}
static void MustReject(Action action, string scenario)
{
    try { action(); }
    catch (JsonException) { Console.WriteLine("REJECTED " + scenario); return; }
    catch (InvalidDataException) { Console.WriteLine("REJECTED " + scenario); return; }
    throw new InvalidOperationException("Unsafe silent recovery: " + scenario);
}

var now = new DateTimeOffset(2026, 11, 7, 12, 0, 0, TimeSpan.Zero);
var root = Path.Combine(Path.GetTempPath(), "blazepisonet-recovery-" + Guid.NewGuid().ToString("N"));
var path = Path.Combine(root, "state.json");
Directory.CreateDirectory(root);
try
{
    Require(Storage.LoadStateFromPath(path, now).RemainingSeconds == 0,
        "actual first-run should initialize zero");
    File.WriteAllText(path, "{");
    MustReject(() => Storage.LoadStateFromPath(path, now), "truncated state");
    File.WriteAllText(path, "null");
    MustReject(() => Storage.LoadStateFromPath(path, now), "null state");
    File.WriteAllText(path, "{\"RemainingSeconds\":2500,\"AppliedEventIds\":null}");
    MustReject(() => Storage.LoadStateFromPath(path, now), "missing paid event identity");
    File.Delete(path);
    File.WriteAllText(path + ".bak", "{\"RemainingSeconds\":1500}");
    MustReject(() => Storage.LoadStateFromPath(path, now), "missing primary with backup");
    File.Delete(path + ".bak");
    File.WriteAllText(path + ".tmp", "{\"RemainingSeconds\":1500}");
    MustReject(() => Storage.LoadStateFromPath(path, now), "missing primary with pending temporary state");
    File.Delete(path + ".tmp");

    var paid = new RuntimeState {
        RemainingSeconds = 3600,
        TimerRunning = true,
        UpdatedUtc = now.AddMinutes(-10),
        AppliedEventIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "coin:source:sequence-1" }
    };
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    var recovered = Storage.LoadStateFromPath(path, now);
    Require(recovered.RemainingSeconds == 3000 && recovered.TimerRunning,
        "valid resume must debit elapsed offline time exactly");
    Require(recovered.AppliedEventIds.Contains("coin:source:sequence-1"),
        "coin dedupe IDs must survive recovery");
    var defaults = new AppConfig();
    Require(!defaults.Enabled && !defaults.DtrEnabled && !defaults.RtsEnabled,
        "new installations must disable coin acceptance and DTR/RTS outputs");
    Console.WriteLine("SERIAL_OUTPUT_DEFAULTS_SAFE_PASS: coin acceptance, DTR and RTS disabled");
    Console.WriteLine("STATE_RECOVERY_GUARD_PASS: 5 fail-closed and 2 positive assertions on production decoder");
    return 0;
}
finally
{
    Directory.Delete(root, recursive: true);
}
