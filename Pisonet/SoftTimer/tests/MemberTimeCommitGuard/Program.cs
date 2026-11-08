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
return 0;
