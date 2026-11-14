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
    // Same production config loader with disposable paths: no installed
    // ProgramData files, live COM ports or operator credentials are touched.
    var configPath = Path.Combine(root, "config.json");
    var initialConfig = Storage.LoadConfigFromPath(configPath);
    var originalConfigText = File.ReadAllText(configPath);
    var originalKey = initialConfig.CentralSharedKey;
    Require(!initialConfig.Enabled && !string.IsNullOrWhiteSpace(originalKey) &&
        !string.IsNullOrWhiteSpace(initialConfig.BlazePwifiControllerId),
        "first install must persist disabled config with stable identity");
    Require(Storage.LoadConfigFromPath(configPath).CentralSharedKey == originalKey,
        "normal restart must preserve coordinator key");

    File.WriteAllText(configPath, "{");
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "corrupt installed configuration must never reset admin or secrets");
    Require(File.ReadAllText(configPath) == "{",
        "corrupt installed configuration must be preserved unchanged");
    File.Delete(configPath);

    File.WriteAllText(configPath + ".bak", originalConfigText);
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "missing installed config with backup evidence");
    Require(!File.Exists(configPath),
        "missing primary with backup must not bootstrap a new identity");
    File.Delete(configPath + ".bak");

    File.WriteAllText(configPath + ".tmp", "uncommitted-config");
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "missing installed config with pending write");
    File.Delete(configPath + ".tmp");

    File.WriteAllText(configPath, originalConfigText);
    File.WriteAllText(configPath + ".tmp", "uncommitted-secret-update");
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "parseable primary with unresolved key change");
    Require(File.ReadAllText(configPath) == originalConfigText &&
        File.ReadAllText(configPath + ".tmp") == "uncommitted-secret-update",
        "pending configuration evidence must survive rejection");
    File.Delete(configPath + ".tmp");

    var invalidIdentity = JsonSerializer.Deserialize<AppConfig>(
        originalConfigText, Storage.JsonOptions)!;
    invalidIdentity.CentralSharedKey = string.Empty;
    File.WriteAllText(configPath, JsonSerializer.Serialize(invalidIdentity, Storage.JsonOptions));
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "installed config missing stable coordinator secret");
    invalidIdentity.CentralSharedKey = originalKey;
    invalidIdentity.BlazePwifiControllerId = string.Empty;
    File.WriteAllText(configPath, JsonSerializer.Serialize(invalidIdentity, Storage.JsonOptions));
    MustReject(() => Storage.LoadConfigFromPath(configPath),
        "installed config missing stable controller identity");
    File.WriteAllText(configPath, originalConfigText);
    Require(Storage.LoadConfigFromPath(configPath).CentralSharedKey == originalKey,
        "repaired evidence must load original coordinator identity");
    Console.WriteLine("CONFIG_FAIL_CLOSED_RECOVERY_PASS");

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
    // A crashed transaction cannot be discarded merely because the last
    // committed primary remains parseable.
    File.WriteAllText(path + ".tmp", "{\"RemainingSeconds\":999999}");
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "valid primary with unresolved pending credit");
    File.Delete(path + ".tmp");

    // A normal File.Replace leaves .bak behind: do NOT reject healthy
    // current state simply because an older backup exists.
    File.WriteAllText(path + ".bak", "{\"legacy\":true}");
    Require(Storage.LoadStateFromPath(path, now).RemainingSeconds == 3000,
        "valid committed primary with backup must remain usable");
    File.Delete(path + ".bak");

    File.WriteAllText(path, "{\"RemainingSeconds\":2500}");
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "parseable incomplete JSON must not invent empty deduplication history");
    paid.UpdatedUtc = now.AddMinutes(10);
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "future paid-state clock cannot extend free time");
    paid.UpdatedUtc = now.AddMinutes(-10);
    paid.RemainingSeconds = -5;
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative remaining time");
    paid.RemainingSeconds = 3600;
    paid.SalesPulseCount = -1;
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative historical sales count");
    paid.SalesPulseCount = 1;
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    var restored = Storage.LoadStateFromPath(path, now);
    Require(restored.RemainingSeconds == 3000 &&
        restored.AppliedEventIds.Contains("COIN:SOURCE:SEQUENCE-1"),
        "valid paid credit and case-insensitive event deduplication must survive restart");
    // A syntactically valid member record cannot carry negative paid time
    // or an invalid revision. Reject on both load and save, before any I/O.
    paid.Members["local"] = new MemberAccount { BankedSeconds = -1 };
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative local member bank");
    paid.Members["local"].BankedSeconds = 0;
    paid.Members["local"].Revision = -1;
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative local member revision");
    paid.Members.Clear();

    paid.RemoteMembers["remote"] = new MemberAccount { BankedSeconds = -60 };
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative remote member bank");
    paid.RemoteMembers["remote"].BankedSeconds = 0;
    paid.RemoteMembers["remote"].Revision = -1;
    File.WriteAllText(path, JsonSerializer.Serialize(paid, Storage.JsonOptions));
    MustReject(() => Storage.LoadStateFromPath(path, now),
        "negative remote member revision");
    paid.RemoteMembers.Clear();

    var invalidMemberSavePath = Path.Combine(root, "invalid-member-save.json");
    paid.Members["local"] = new MemberAccount { BankedSeconds = -1 };
    MustReject(() => Storage.SaveStateToPath(invalidMemberSavePath, paid, now),
        "reject invalid local member before state save");
    Require(!File.Exists(invalidMemberSavePath) &&
        !File.Exists(invalidMemberSavePath + ".tmp"),
        "invalid financial snapshot must never reach disk");
    paid.Members.Clear();
    Console.WriteLine("STATE_MEMBER_ACCOUNT_VALIDATION_PASS");

    Console.WriteLine("STATE_RECOVERY_INTERRUPTED_WRITE_PASS");
    Console.WriteLine("STATE_RECOVERY_REQUIRED_FIELDS_AND_CLOCK_PASS");
    Console.WriteLine("STATE_RECOVERY_CASE_INSENSITIVE_DEDUP_PASS");

    var writePath = Path.Combine(root, "atomic.json");
    Storage.AtomicWrite(writePath, "first");
    Require(File.ReadAllText(writePath) == "first" &&
        !File.Exists(writePath + ".tmp"),
        "first write must leave a committed primary without temporary data");
    Storage.AtomicWrite(writePath, "second");
    Require(File.ReadAllText(writePath) == "second" &&
        File.ReadAllText(writePath + ".bak") == "first" &&
        !File.Exists(writePath + ".tmp"),
        "replacement must retain previous backup and not leave a temporary file");
    File.WriteAllText(writePath + ".tmp", "unresolved-third-credit");
    MustReject(() => Storage.AtomicWrite(writePath, "third"),
        "existing pending state must not be overwritten by a new credit");
    Require(File.ReadAllText(writePath) == "second" &&
        File.ReadAllText(writePath + ".bak") == "first" &&
        File.ReadAllText(writePath + ".tmp") == "unresolved-third-credit",
        "a rejected write must preserve primary, backup and pending evidence");
    Console.WriteLine("STATE_ATOMIC_WRITE_GUARD_PASS: replace, backup and unresolved temporary preservation");

    // Financial regression: the previous writer silently removed older IDs
    // above 2,048 entries. A later duplicate could then be credited again.
    var historyPath = Path.Combine(root, "large-paid-state.json");
    var historicalId = "coin:oldest:already-paid";
    var allIds = Enumerable.Range(0, 2600).Select(i => $"coin:entry:{i:0000}")
        .Append(historicalId).ToHashSet(StringComparer.OrdinalIgnoreCase);
    var beforeSave = now.AddMinutes(-17);
    var largeState = new RuntimeState {
        RemainingSeconds = 4300,
        TimerRunning = true,
        UpdatedUtc = beforeSave,
        SalesPulseCount = 2601,
        AppliedEventIds = allIds
    };
    Storage.SaveStateToPath(historyPath, largeState, now);
    Require(largeState.AppliedEventIds.Count == 2601 &&
        largeState.UpdatedUtc == beforeSave &&
        largeState.AppliedEventIds.Contains(historicalId),
        "persistence must not mutate caller-owned timestamps or event history");
    var largeRecovered = Storage.LoadStateFromPath(historyPath, now);
    Require(largeRecovered.AppliedEventIds.Count == 2601 &&
        largeRecovered.AppliedEventIds.Contains("COIN:OLDEST:ALREADY-PAID") &&
        largeRecovered.SalesPulseCount == 2601 &&
        largeRecovered.RemainingSeconds == 4300,
        "recovery must retain every older event and sales total after the 2048 threshold");
    largeState.AppliedEventIds.Add("coin:new-credit");
    Storage.SaveStateToPath(historyPath, largeState, now);
    var afterSecondSave = Storage.LoadStateFromPath(historyPath, now);
    Require(afterSecondSave.AppliedEventIds.Count == 2602 &&
        afterSecondSave.AppliedEventIds.Contains(historicalId) &&
        afterSecondSave.AppliedEventIds.Contains("coin:new-credit"),
        "a subsequent credit must retain deduplication of older coins");
    Require(File.Exists(historyPath + ".bak"),
        "successful replacement must leave previous committed history as backup");
    File.WriteAllText(historyPath + ".tmp", "unresolved paid credit");
    MustReject(() => Storage.SaveStateToPath(historyPath, largeState, now),
        "pending financial write cannot discard historical replay evidence");
    Require(largeState.UpdatedUtc == beforeSave &&
        largeState.AppliedEventIds.Count == 2602 &&
        File.ReadAllText(historyPath + ".tmp") == "unresolved paid credit",
        "failed state save must not alter the original state or pending evidence");
    Console.WriteLine("STATE_EVENT_HISTORY_NOT_PRUNED_PASS: 2602 IDs preserved and old coin remains deduplicated");
    Console.WriteLine("STATE_SAVE_CALLER_IMMUTABLE_PASS");

    var defaults = new AppConfig();
    Require(!defaults.Enabled && !defaults.DtrEnabled && !defaults.RtsEnabled,
        "new installations must disable coin acceptance and DTR/RTS outputs");
    Console.WriteLine("SERIAL_OUTPUT_DEFAULTS_SAFE_PASS: coin acceptance, DTR and RTS disabled");
    Console.WriteLine("STATE_RECOVERY_GUARD_PASS: startup, interrupted write, required fields, clock, accounting and dedupe source-linked checks");
    return 0;
}
finally
{
    Directory.Delete(root, recursive: true);
}
