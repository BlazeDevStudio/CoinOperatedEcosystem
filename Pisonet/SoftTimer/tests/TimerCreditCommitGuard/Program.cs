// Exercises actual production TimerEngine.AddCoin/AddSeconds with injected disk
// faults. Never touches ProgramData or an actual serial adapter.
using System.IO;
using BlazePisonet.SoftTimer;

static void Require(bool condition, string reason)
{
    if (!condition) throw new InvalidOperationException(reason);
}
static void MustThrow(Action action, string what)
{
    try { action(); }
    catch (IOException) { Console.WriteLine("DENIED " + what); return; }
    catch (InvalidOperationException) { Console.WriteLine("DENIED " + what); return; }
    throw new InvalidOperationException("Unexpected financial acceptance: " + what);
}

var initial = new RuntimeState {
    RemainingSeconds = 120,
    TimerRunning = true,
    SalesPulseCount = 7,
    AppliedEventIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "existing-event" }
};
var failingWrites = 0;
using (var engine = new TimerEngine(initial, candidate =>
{
    failingWrites++;
    Require(candidate.RemainingSeconds == 420 && candidate.SalesPulseCount == 8,
        "staged credit must be computed before attempted durable save");
    Require(candidate.AppliedEventIds.Contains("coin:com9"),
        "staged event must retain deduplication ID");
    throw new IOException("synthetic disk failure");
}, startTicker: false))
{
    var callbacks = 0;
    engine.RemainingChanged += _ => callbacks++;
    engine.ActiveChanged += _ => callbacks++;
    MustThrow(() => engine.AddSeconds(300, "coin:COM9", true, "lab"),
        "initial save fails");
    Require(engine.RemainingSeconds == 120 && engine.SalesPulseCount == 7,
        "failed save mutated visible paid balance / sale count");
    Require(!initial.AppliedEventIds.Contains("coin:COM9"),
        "failed save mutated original deduplication set");
    Require(engine.CreditPersistenceFaulted && callbacks == 0,
        "failed save must permanently latch fault and suppress success callbacks");
    MustThrow(() => engine.AddSeconds(300, "coin:COM9", true, "retry"),
        "retry after uncertain save");
    Require(failingWrites == 1, "an ambiguous credit must not be retried");
    // Real production periodic callback must not continue debiting or
    // persist again from a ThreadPool thread after a storage write fault.
    var lastTick = typeof(TimerEngine).GetField("_lastTickStamp",
        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
        ?? throw new Exception("Timer source tick clock not found");
    lastTick.SetValue(engine,
        System.Diagnostics.Stopwatch.GetTimestamp() -
        10L * System.Diagnostics.Stopwatch.Frequency);
    var tick = typeof(TimerEngine).GetMethod("Tick",
        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
        ?? throw new Exception("Actual timer Tick source not found");
    tick.Invoke(engine, null);
    Require(engine.RemainingSeconds == 120 && failingWrites == 1,
        "credit disk fault must freeze countdown without new saves");
    Console.WriteLine("COIN_FAULT_FREEZES_TIMER_TICK_PASS");

}
Console.WriteLine("COIN_FAILED_PERSISTENCE_DENIED_PASS");

var successfulWrites = 0;
RuntimeState? diskState = null;
var good = new RuntimeState { RemainingSeconds = 10 };
using (var engine = new TimerEngine(good, state =>
{
    successfulWrites++;
    diskState = state;
}, startTicker: false))
{
    var callbacks = 0;
    engine.RemainingChanged += x =>
    {
        Require(diskState is not null && diskState.RemainingSeconds == x,
            "timer event was announced before saving it");
        callbacks++;
    };
    Require(engine.AddSeconds(90, "coin:one", true, "lab"),
        "valid first coin not accepted");
    Require(engine.RemainingSeconds == 100 && engine.SalesPulseCount == 1,
        "valid first credit amount incorrect");
    Require(engine.AddSeconds(90, "coin:TWO", true, "lab"),
        "second distinct event denied");
    Require(engine.RemainingSeconds == 190 && engine.SalesPulseCount == 2,
        "second credit amount incorrect");
    Require(!engine.AddSeconds(90, "coin:two", true, "duplicate"),
        "case-insensitive duplicate event was recredited");
    Require(successfulWrites == 2 && callbacks == 2,
        "duplicate or failed credit caused persistence / callbacks");
    Require(diskState is not null && diskState.AppliedEventIds.Contains("coin:one") &&
            diskState.AppliedEventIds.Contains("coin:TWO"),
        "persisted event identities missing");
}
Console.WriteLine("COIN_COMMITTED_BEFORE_ANNOUNCEMENT_PASS");

var overflow = new RuntimeState {
    RemainingSeconds = long.MaxValue,
    AppliedEventIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
};
var overflowWrites = 0;
try
{
    TimerEngine.TryPersistCredit(overflow, 1, "overflow", true,
        _ => overflowWrites++, out _);
    throw new Exception("overflow accepted");
}
catch (OverflowException) { }
Require(overflowWrites == 0 && overflow.RemainingSeconds == long.MaxValue &&
    !overflow.AppliedEventIds.Contains("overflow"),
    "overflow must not mutate or persist paid balance");
Console.WriteLine("COIN_OVERFLOW_REJECTED_PASS");

// Source-linked ThreadPool countdown regression: a scheduled 5s checkpoint
// must neither throw nor mutate the published balance after failed storage.
var tickMethod = typeof(TimerEngine).GetMethod("Tick",
    System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
    ?? throw new Exception("TimerEngine.Tick production source unavailable");
var tickTimestamp = typeof(TimerEngine).GetField("_lastTickStamp",
    System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)
    ?? throw new Exception("TimerEngine monotonic tick field unavailable");
var faultedCountdownWrites = 0;
var faultedTickSource = new RuntimeState { RemainingSeconds = 120, TimerRunning = true };
using (var engine = new TimerEngine(faultedTickSource, staged =>
{
    faultedCountdownWrites++;
    Require(staged.RemainingSeconds < 120, "countdown did not stage elapsed debit");
    throw new IOException("simulated periodic checkpoint storage loss");
}, startTicker: false))
{
    var callbacks = 0;
    engine.RemainingChanged += _ => callbacks++;
    engine.ActiveChanged += _ => callbacks++;
    tickTimestamp.SetValue(engine,
        System.Diagnostics.Stopwatch.GetTimestamp() -
        3L * System.Diagnostics.Stopwatch.Frequency);
    tickMethod.Invoke(engine, null);  // MUST NOT throw TargetInvocationException
    Require(engine.CreditPersistenceFaulted && engine.RemainingSeconds == 120 &&
        faultedTickSource.RemainingSeconds == 120 && callbacks == 0,
        "failed periodic checkpoint leaked paid seconds or emitted a success event");
    tickMethod.Invoke(engine, null);
    Require(faultedCountdownWrites == 1,
        "countdown automatically retried after uncertain storage state");
}
Console.WriteLine("TIMER_PERIODIC_WRITE_FAILURE_FAILS_CLOSED_PASS");

RuntimeState? successfulTickCheckpoint = null;
using (var engine = new TimerEngine(
    new RuntimeState { RemainingSeconds = 120, TimerRunning = true },
    staged => successfulTickCheckpoint = staged, startTicker: false))
{
    long? announced = null;
    engine.RemainingChanged += s =>
    {
        Require(successfulTickCheckpoint?.RemainingSeconds == s,
            "countdown was announced before durable checkpoint");
        announced = s;
    };
    tickTimestamp.SetValue(engine,
        System.Diagnostics.Stopwatch.GetTimestamp() -
        2L * System.Diagnostics.Stopwatch.Frequency);
    tickMethod.Invoke(engine, null);
    Require(!engine.CreditPersistenceFaulted && engine.RemainingSeconds == 118 &&
        successfulTickCheckpoint?.RemainingSeconds == 118 && announced == 118,
        "good countdown checkpoint did not debit/persist/notify in order");
}
Console.WriteLine("TIMER_PERIODIC_WRITE_SUCCESS_ORDER_PASS");
return 0;
