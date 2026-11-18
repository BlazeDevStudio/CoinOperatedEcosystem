#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconDurableJournal.h"
using namespace blaze_journal;
using namespace blaze_credit;

struct FakeFlash {
  struct Slot { bool exists=false; size_t length=0; uint8_t bytes[RECORD_SIZE]={}; } slot[2];
  enum Fault { Normal, BeforeWrite, AfterCommitUncertain, TornAlternate, ReadFault } fault=Normal;
  static int index(char c){return c=='A'?0:c=='B'?1:-1;}
  static bool read(void*ctx,char c,uint8_t out[RECORD_SIZE],size_t&actual){
    auto& f=*static_cast<FakeFlash*>(ctx);
    const int n=index(c);if(n<0||f.fault==ReadFault)return false;
    actual=f.slot[n].exists?f.slot[n].length:0;
    if(actual==RECORD_SIZE)memcpy(out,f.slot[n].bytes,RECORD_SIZE);
    return true;
  }
  static bool write(void*ctx,char c,const uint8_t data[RECORD_SIZE]){
    auto& f=*static_cast<FakeFlash*>(ctx);
    const int n=index(c);if(n<0||f.fault==BeforeWrite)return false;
    auto& dest=f.slot[n];
    dest.exists=true;
    dest.length=RECORD_SIZE;
    memcpy(dest.bytes,data,RECORD_SIZE);
    if(f.fault==AfterCommitUncertain)return false;
    if(f.fault==TornAlternate){
      dest.length=23; // simulates power cut during inactive slot replacement
      return false;
    }
    return true;
  }
  IO port(){return {&FakeFlash::read,&FakeFlash::write,this};}
};
static Snapshot getSlave(const Journal&j){
  Snapshot s={};
  s.authorizedIssuer=j.record().p.issuer;
  s.lastSequence=j.record().p.sequence;
  s.remainingUnits=j.record().p.remainingUnits;
  s.paidEventCount=j.record().p.paidCount;
  s.lastSeconds=j.record().p.lastSeconds;
  return s;
}
int main(){
  FakeFlash fs={};
  Journal j(fs.port(),Kind::Slave);
  assert(j.recover()==Status::Empty);
  const Payload start={0xAABBCCDD,0,0,0,0,0,0};
  assert(j.initialize(start));
  assert(j.ready()&&j.record().generation==1&&j.activeSlot()=='A');
  // No direct unbilled credit, identity change or sequence reset is allowed.
  Record forged=j.record();
  forged.p.remainingUnits=1000000ULL;
  assert(!j.commit(forged));
  forged=j.record();
  forged.p.issuer=0xCAFEBABE;
  assert(!j.commit(forged));
  Snapshot balance=getSlave(j);
  assert(apply(balance,{0xAABBCCDD,1,60},commitSlaveSnapshot,&j)==Outcome::Applied);
  assert(j.activeSlot()=='B'&&j.record().generation==2);
  assert(j.record().p.remainingUnits==6000000ULL);
  // Countdown checkpoints may decrease, never increase, the journal balance.
  Record illegal=j.record();
  illegal.p.remainingUnits+=100000ULL;
  assert(!j.commit(illegal));
  // Receiver committed but ACK lost: re-read real slot bytes, reject replay.
  Journal restarted(fs.port(),Kind::Slave);
  assert(restarted.recover()==Status::Ready);
  assert(restarted.record().generation==2);
  Snapshot afterRestart=getSlave(restarted);
  assert(apply(afterRestart,{0xAABBCCDD,1,60},commitSlaveSnapshot,&restarted)==Outcome::Duplicate);
  assert(restarted.record().generation==2);
  // Attempted commit that wrote a VALID slot but reported an I/O error is
  // UNCERTAIN; RAM must not advance or ACK until reboot and reconciliation.
  fs.fault=FakeFlash::AfterCommitUncertain;
  const Snapshot beforeUncertain=afterRestart;
  assert(apply(afterRestart,{0xAABBCCDD,2,30},commitSlaveSnapshot,&restarted)==Outcome::NotDurable);
  assert(restarted.status()==Status::Uncertain);
  assert(afterRestart.lastSequence==beforeUncertain.lastSequence);
  fs.fault=FakeFlash::Normal;
  Journal reboot2(fs.port(),Kind::Slave);
  assert(reboot2.recover()==Status::Ready);
  assert(reboot2.record().p.sequence==2);
  Snapshot s2=getSlave(reboot2);
  assert(apply(s2,{0xAABBCCDD,2,30},commitSlaveSnapshot,&reboot2)==Outcome::Duplicate);
  assert(s2.remainingUnits==9000000ULL);
  // Torn write of inactive slot must never be silently treated as settled.
  fs.fault=FakeFlash::TornAlternate;
  assert(apply(s2,{0xAABBCCDD,3,15},commitSlaveSnapshot,&reboot2)==Outcome::NotDurable);
  fs.fault=FakeFlash::Normal;
  Journal torn(fs.port(),Kind::Slave);
  assert(torn.recover()==Status::Degraded);
  assert(!torn.ready()); // manual/ledger reconciliation required
  assert(torn.record().p.sequence==2);
  // A zero-length read fault also rejects transactions.
  fs.fault=FakeFlash::ReadFault;
  Journal badIO(fs.port(),Kind::Slave);
  assert(badIO.recover()==Status::IoError);
  // Wrong configured master prevents credit even with a valid record.
  fs.fault=FakeFlash::Normal;
  Journal wrongKind(fs.port(),Kind::Master);
  assert(wrongKind.recover()==Status::WrongKind);

  FakeFlash mf={};
  Journal master(mf.port(),Kind::Master);
  assert(master.recover()==Status::Empty);
  const Payload m0={0x12345678,0,0,0,0,0,0};
  assert(master.initialize(m0));
  MasterPending mp={};
  assert(stage(mp,120,commitMasterPending,&master));
  assert(master.record().p.sequence==1&&master.record().p.pendingSequence==1);
  assert(!stage(mp,120,commitMasterPending,&master)); // one unpaid event only
  Record illegalMaster=master.record();
  illegalMaster.p.pendingSequence=0;
  illegalMaster.p.pendingSeconds=0;
  illegalMaster.p.sequence=1;
  illegalMaster.p.remainingUnits=100000ULL;
  assert(!master.commit(illegalMaster));
  Journal masterRestart(mf.port(),Kind::Master);
  assert(masterRestart.recover()==Status::Ready);
  MasterPending pending={masterRestart.record().p.sequence,
                         masterRestart.record().p.pendingSequence,
                         masterRestart.record().p.pendingSeconds};
  assert(pending.pendingSequence==1&&pending.pendingSeconds==120);
  assert(settle(pending,1,commitMasterPending,&masterRestart));
  assert(masterRestart.record().p.pendingSequence==0);
  // Incorrect role or corrupt CRC cannot be made healthy by guesswork.
  mf.slot[0].bytes[38]^=0x01;
  Journal degraded(mf.port(),Kind::Master);
  assert(degraded.recover()==Status::Degraded);
  mf.slot[1].bytes[38]^=0x01;
  Journal corrupted(mf.port(),Kind::Master);
  assert(corrupted.recover()==Status::Corrupt);
  puts("PASS: dual slots, CRC, atomic event/balance, lost ACK, reboot, torn write, uncertain result, pending Master");
}
