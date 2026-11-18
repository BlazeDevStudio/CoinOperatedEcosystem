// Host-side fault injection on the actual INTERCON journal implementation.
// Simulates power loss while writing each possible prefix of a 76-byte slot.
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconDurableJournal.h"

using namespace blaze_durable;
using blaze_credit::Outcome;
struct FakeSlots final : Storage {
  std::array<uint8_t,RECORD_BYTES> bytes[2]={};
  size_t len[2]={0,0};
  bool exists[2]={false,false};
  bool ioError=false;
  int tearAt=-1;
  bool writeFullButReportFailure=false;
  Read readSlot(uint8_t slot,uint8_t* dst,size_t max,size_t& n) override {
    if(slot>1||ioError)return Read::Error;
    if(!exists[slot]){n=0;return Read::Missing;}
    n=len[slot];
    if(n<=max)memcpy(dst,bytes[slot].data(),n);
    return Read::Present;
  }
  bool writeSlot(uint8_t slot,const uint8_t* src,size_t n) override {
    if(slot>1||n!=RECORD_BYTES||ioError)return false;
    exists[slot]=true;
    if(tearAt>=0){
      len[slot]=(size_t)tearAt;
      memcpy(bytes[slot].data(),src,len[slot]);
      return false;
    }
    len[slot]=n;
    memcpy(bytes[slot].data(),src,n);
    return !writeFullButReportFailure;
  }
};
int main(){
  constexpr uint32_t SLAVE=0x0011ABCD;
  constexpr uint32_t MASTER=0x00FFAA11;
  FakeSlots base;
  Journal j(base);
  assert(j.load(Role::Slave,SLAVE,MASTER)==Load::Missing);
  assert(j.initialize(Role::Slave,SLAVE,MASTER,300ULL*100000ULL));
  assert(j.ready()&&j.record().generation==1);
  assert(j.applySlave({MASTER,1,60})==Outcome::Applied);
  assert(j.record().generation==2);
  assert(j.record().slave.remainingUnits==360ULL*100000ULL);
  assert(j.applySlave({MASTER,1,60})==Outcome::Duplicate);
  assert(j.applySlave({MASTER,1,90})==Outcome::Conflict);
  assert(j.applySlave({MASTER,3,90})==Outcome::OutOfOrder);
  assert(j.applySlave({SLAVE,2,90})==Outcome::WrongIssuer);
  Journal fresh(base);
  assert(fresh.load(Role::Slave,SLAVE,MASTER)==Load::Ready);
  assert(fresh.record().slave.lastSequence==1);
  assert(fresh.applySlave({MASTER,1,60})==Outcome::Duplicate);
  assert(fresh.checkpointRemaining(359ULL*100000ULL));
  assert(!fresh.checkpointRemaining(400ULL*100000ULL));
  assert(fresh.record().generation==3);
  assert(fresh.applySlave({MASTER,2,30})==Outcome::Applied);
  assert(fresh.record().slave.remainingUnits==389ULL*100000ULL);
  Journal after(base);
  assert(after.load(Role::Slave,SLAVE,MASTER)==Load::Ready);
  assert(after.applySlave({MASTER,2,30})==Outcome::Duplicate);
  assert(after.load(Role::Slave,MASTER,SLAVE)==Load::BindingMismatch);
  assert(!after.initialize(Role::Slave,SLAVE,MASTER));
  // Overwrite a noncanonical reserved byte. Even when the other valid slot
  // remains present, rejecting the whole store prevents balance rollback.
  FakeSlots bad=base;
  bad.bytes[0][43]^=1;
  Journal corrupt(bad);
  assert(corrupt.load(Role::Slave,SLAVE,MASTER)==Load::Corrupt);
  assert(!corrupt.ready());
  assert(!corrupt.initialize(Role::Slave,SLAVE,MASTER));
  // Losing either post-genesis slot must not roll balance back a credit.
  FakeSlots vanished=base;
  vanished.exists[0]=false;
  Journal noOldSlot(vanished);
  assert(noOldSlot.load(Role::Slave,SLAVE,MASTER)==Load::Corrupt);
  vanished=base;vanished.exists[1]=false;
  Journal noNewSlot(vanished);
  assert(noNewSlot.load(Role::Slave,SLAVE,MASTER)==Load::Corrupt);
  // Even a correctly checksummed old snapshot cannot silently overwrite
  // a later acknowledged credit when generation continuity is broken.
  FakeSlots gap=base;
  Record oldRecord={};
  assert(deserialize(gap.bytes[0].data(),RECORD_BYTES,oldRecord));
  oldRecord.generation=1;
  assert(serialize(oldRecord,gap.bytes[0].data()));
  Journal generationGap(gap);
  assert(generationGap.load(Role::Slave,SLAVE,MASTER)==Load::Corrupt);

  // Work from both valid slots. On every partial write of the inactive slot,
  // remote credit acceptance becomes uncertain and the reboot must LOCK.
  for(size_t cut=0;cut<RECORD_BYTES;cut++){
    FakeSlots torn=base;
    Journal runtime(torn);
    assert(runtime.load(Role::Slave,SLAVE,MASTER)==Load::Ready);
    const uint64_t oldBalance=runtime.record().slave.remainingUnits;
    torn.tearAt=(int)cut;
    assert(runtime.applySlave({MASTER,3,10})==Outcome::NotDurable);
    assert(!runtime.ready());
    assert(runtime.record().slave.remainingUnits==oldBalance);
    torn.tearAt=-1;
    Journal reboot(torn);
    assert(reboot.load(Role::Slave,SLAVE,MASTER)==Load::Corrupt);
    assert(!reboot.ready());
  }
  // Simulate a write fully hitting flash but its IO return/ACK getting lost.
  // A reboot must load the NEW record and deduplicate the retransmitted coin.
  FakeSlots uncertain=base;
  Journal beforeCrash(uncertain);
  assert(beforeCrash.load(Role::Slave,SLAVE,MASTER)==Load::Ready);
  uncertain.writeFullButReportFailure=true;
  assert(beforeCrash.applySlave({MASTER,3,10})==Outcome::NotDurable);
  uncertain.writeFullButReportFailure=false;
  Journal afterCrash(uncertain);
  assert(afterCrash.load(Role::Slave,SLAVE,MASTER)==Load::Ready);
  assert(afterCrash.record().slave.lastSequence==3);
  assert(afterCrash.applySlave({MASTER,3,10})==Outcome::Duplicate);
  assert(afterCrash.applySlave({MASTER,4,1})==Outcome::Applied);

  // Persist the MASTER pending coin before sending it. Crash and lost ACK
  // cannot generate a second event, and a stale ACK cannot clear the first.
  FakeSlots masterStorage;
  Journal m(masterStorage);
  assert(m.initialize(Role::Master,MASTER,SLAVE));
  assert(m.stageMaster(60));
  assert(m.record().master.pendingSequence==1);
  assert(!m.stageMaster(20));
  Journal masterReboot(masterStorage);
  assert(masterReboot.load(Role::Master,MASTER,SLAVE)==Load::Ready);
  assert(masterReboot.record().master.pendingSequence==1);
  assert(!masterReboot.settleMaster(2));
  assert(masterReboot.settleMaster(1));
  Journal afterAck(masterStorage);
  assert(afterAck.load(Role::Master,MASTER,SLAVE)==Load::Ready);
  assert(afterAck.record().master.pendingSequence==0);
  assert(afterAck.stageMaster(120));
  assert(afterAck.record().master.pendingSequence==2);
  assert(afterAck.record().master.pendingSeconds==120);
  // Candidate writes never run if max balance would be exceeded.
  FakeSlots maxSlots;
  Journal maxJ(maxSlots);
  assert(maxJ.initialize(Role::Slave,SLAVE,MASTER,blaze_credit::MAX_UNITS));
  assert(maxJ.applySlave({MASTER,1,1})==Outcome::Overflow);
  assert(maxJ.record().generation==1);
  std::puts("PASS: dual-slot journal / CRC / peer binding / 76 torn writes / ACK loss / reboot / credit idempotency");
  return 0;
}
