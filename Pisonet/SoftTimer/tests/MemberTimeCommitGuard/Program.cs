// Source-linked member-time transaction tests. Pure deterministic test state;
// no registry, serial adapter, actual ProgramData or physical coin involved.
using BlazePisonet.SoftTimer;
using System.IO;

static void Require(bool ok, string message)
{
    if (!ok) throw new InvalidOperationException(message);
}

static MemberAccount Account(string name, string password, long bank)
{
    var key = Passwords.HashMemberPassword(password);
    return new MemberAccount
    {
        Username = name,
        PasswordScheme = "pbkdf2-sha256",
        PasswordSalt = key.Salt,
        PasswordHash = key.Hash,
        PasswordRounds = 120000,
        BankedSeconds = bank
    };
}
var alice = Account("alice", "test-secret-a", 200);
var bob = Account("bob", "test-secret-b", 15);
static RuntimeState Seed(MemberAccount a, MemberAccount b) => new()
{
    RemainingSeconds = 120,
    TimerRunning = true,
    SalesPulseCount = 9,
    Members = new Dictionary<string, MemberAccount>(StringComparer.OrdinalIgnoreCase)
    {
        [a.Username] = a, [b.Username] = b
    }
};

static void FailCase(string label, MemberAccount a, MemberAccount b,
    Action<TimerEngine> attempt)
{
    var seed = Seed(a, b);
    var writes = 0;
    var signals = 0;
    using var engine = new TimerEngine(seed, staged =>
    {
        writes++;
        throw new IOException("simulated storage write failure: " + label);
    }, startTicker: false);
    engine.RemainingChanged += _ => signals++;
    engine.ActiveChanged += _ => signals++;
    engine.Audit += _ => signals++;
    try { attempt(engine); throw new Exception("Unsafe success: " + label); }
    catch (IOException) { }
    Require(engine.CreditPersistenceFaulted, label + ": failure must latch lockout");
    Require(writes == 1 && signals == 0,
        label + ": no repeat write or success callback on failure");
    Require(engine.RemainingSeconds == 120 && engine.SalesPulseCount == 9,
        label + ": remaining or sale count mutated before successful write");
    var accounts = engine.MembersSnapshot();
    Require(accounts.Single(x => x.Username == "alice").BankedSeconds == a.BankedSeconds &&
        accounts.Single(x => x.Username == "bob").BankedSeconds == b.BankedSeconds,
        label + ": member banks mutated despite failed write");
    Require(seed.Members["alice"].BankedSeconds == a.BankedSeconds &&
        seed.Members["bob"].BankedSeconds == b.BankedSeconds,
        label + ": original account reference mutated despite failed write");
    try { attempt(engine); throw new Exception("Retry permitted after uncertain save"); }
    catch (InvalidOperationException) { }
    Require(writes == 1, label + ": uncertain write retried");
    Console.WriteLine("MEMBER_FAIL_CLOSED_PASS: " + label);
}

FailCase("bank", alice, bob, e =>
    Require(e.BankCurrentTime("alice", "test-secret-a"), "bank denied unexpectedly"));
FailCase("restore", alice, bob, e =>
    Require(e.RestoreMemberTime("alice", "test-secret-a"), "restore denied unexpectedly"));
FailCase("transfer", alice, bob, e =>
    Require(e.TransferMemberTime("alice", "test-secret-a", "bob", 40), "transfer denied unexpectedly"));
FailCase("member-update", alice, bob, e =>
    Require(e.CreateOrUpdateMember("alice", "new-test-password"), "update denied unexpectedly"));

var saves = 0;
RuntimeState? durable = null;
var original = Seed(alice, bob);
using (var engine = new TimerEngine(original, candidate =>
{
    saves++;
    durable = candidate;
    Require(candidate.Members["alice"].BankedSeconds >= 0, "invalid staged account");
}, startTicker: false))
{
    var eventCount = 0;
    engine.RemainingChanged += seconds =>
    {
        Require(durable is not null && durable.RemainingSeconds == seconds,
            "announced member balance without durable state");
        eventCount++;
    };
    Require(engine.BankCurrentTime("alice", "test-secret-a"), "bank failed");
    Require(engine.RemainingSeconds == 0 && durable?.Members["alice"].BankedSeconds == 320,
        "120 seconds were not banked");
    Require(original.RemainingSeconds == 120 && original.Members["alice"].BankedSeconds == 200,
        "original state mutated by successful clone");
    Require(engine.RestoreMemberTime("alice", "test-secret-a"), "restore failed");
    Require(engine.RemainingSeconds == 320 && durable?.Members["alice"].BankedSeconds == 0,
        "restore must move exactly the banked seconds");
    Require(engine.TransferMemberTime("bob", "test-secret-b", "alice", 10), "transfer failed");
    Require(durable?.Members["alice"].BankedSeconds == 10 &&
        durable?.Members["bob"].BankedSeconds == 5,
        "member transfer did not preserve total banked time");
    Require(saves == 3 && eventCount == 2,
        "unexpected duplicate write or early notification");
    Require(!engine.TransferMemberTime("bob", "bad-pass", "alice", 1),
        "bad credentials transferred member time");
    Require(saves == 3, "invalid credentials triggered disk write");
}
Console.WriteLine("MEMBER_PERSIST_BEFORE_PUBLISH_PASS");

var pending = new PendingMemberOperation
{
    Action = "member_bank", Username = "alice", MemberToken = "alice",
    EventId = "pending:event:1", Seconds = 120, MemberRevision = 1
};
FailCase("pending-record", alice, bob, e => e.SetPendingMemberOperation(pending));
FailCase("bank-reset", alice, bob, e => e.Reset("confirmed remote bank"));

var clearSeed = Seed(alice, bob);
clearSeed.PendingMemberOperation = pending;
var clearWrites = 0;
using (var engine = new TimerEngine(clearSeed, _ =>
{
    clearWrites++;
    throw new IOException("failed pending clear");
}, startTicker: false))
{
    try { engine.ClearPendingMemberOperation(pending.EventId); throw new Exception("Clear unexpectedly persisted"); }
    catch (IOException) { }
    Require(engine.CreditPersistenceFaulted && clearWrites == 1 &&
        engine.PendingMemberOperation?.EventId == pending.EventId &&
        clearSeed.PendingMemberOperation?.EventId == pending.EventId,
        "failed pending-clear discarded replay evidence");
}
Console.WriteLine("PENDING_MEMBER_CLEAR_FAILURE_PRESERVED_PASS");

var remote = Account("remote", "remote-test", 50);
var remoteOriginalManaged = remote.RemoteManaged;
using (var engine = new TimerEngine(Seed(alice, bob), _ =>
{
    throw new IOException("remote snapshot persist failure");
}, startTicker: false))
{
    try
    {
        engine.ApplyRemoteMembers(new[] { remote }, 17);
        throw new Exception("Remote member write unexpectedly succeeded");
    }
    catch (IOException) { }
    Require(engine.CreditPersistenceFaulted && engine.RemoteMemberRevision == 0 &&
        engine.RemoteMembersSnapshot().Count == 0 && remote.RemoteManaged == remoteOriginalManaged,
        "failed remote snapshot changed published revision or caller-owned objects");
}
Console.WriteLine("REMOTE_SNAPSHOT_FAILED_WRITE_PRESERVED_PASS");

var replayWrites = 0;
RuntimeState? lastDurable = null;
using (var engine = new TimerEngine(Seed(alice, bob), saved =>
{
    replayWrites++;
    lastDurable = saved;
}, startTicker: false))
{
    engine.SetPendingMemberOperation(pending);
    Require(engine.PendingMemberOperation?.EventId == pending.EventId &&
        lastDurable?.PendingMemberOperation?.EventId == pending.EventId,
        "pending operation was not durably recorded");
    pending.EventId = "mutated-outside-engine";
    Require(engine.PendingMemberOperation?.EventId == "pending:event:1",
        "caller mutated a committed pending transaction by alias");
    engine.Reset("remote bank committed");
    Require(engine.RemainingSeconds == 0 &&
        lastDurable?.PendingMemberOperation?.EventId == "pending:event:1",
        "confirmed bank reset must retain pending reconciliation record");
    engine.ClearPendingMemberOperation("pending:event:1");
    Require(engine.PendingMemberOperation is null && lastDurable?.PendingMemberOperation is null,
        "pending operation not durably cleared");
    Require(replayWrites == 3, "expected exactly three durable pending/reset/clear writes");
}
Console.WriteLine("PENDING_REPLAY_ORDER_AND_NO_ALIAS_PASS");
return 0;
