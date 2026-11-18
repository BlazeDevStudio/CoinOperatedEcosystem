// INTERCON Stage 3 — host simulator for exact production on-flash image codec.
// No payment hardware claims: fault injection models pre-rename / post-rename
// crash boundaries, not real flash chips, brownouts, or LittleFS wear.
#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconJournalCodec.h"
using namespace blaze_journal;
namespace {
struct Flash {
  uint8_t slot[2][IMAGE_BYTES]={};
  bool present[2]={false,false};
  bool failWrite=false,failRename=false,failPostRename=false;
  Binding expected={0xAABBCCDD,0x11223344,0x37B91362,ROLE_SLAVE};
  Recovered current={};
  void recover(){
    current=inspect(present[0],slot[0],present[1],slot[1],expected);
  }
  bool init(){
    if(present[0]||present[1])return false;
    Record r={};
    r.bind=expected;r.generation=1;
    r.slave.authorizedIssuer=expected.peer;
    uint8_t out[IMAGE_BYTES]={};
    if(!encode(r,out))return false;
    memcpy(slot[0],out,IMAGE_BYTES);
    memcpy(slot[1],out,IMAGE_BYTES);
    present[0]=present[1]=true;
    recover();
    return current.status==Status::Healthy;
  }
  bool commit(const Record& newState){
    Record candidate={};uint8_t index=0;
    if(!next(current,newState,candidate,index))return false;
    uint8_t tmp[IMAGE_BYTES]={};
    if(!encode(candidate,tmp))return false;
    if(failWrite || failRename)return false; // old slots remain
    memcpy(slot[index],tmp,IMAGE_BYTES);
    present[index]=true;
    if(failPostRename)return false; // ACK not sent, flash *might* have commit
    recover();
    return current.status==Status::Healthy &&
           current.snapshot.generation==candidate.generation;
  }
};
struct SlaveTxn {
  Flash* flash;
  Record proposed;
  bool write(const blaze_credit::Snapshot& s) {
    proposed=flash->current.snapshot;
    proposed.slave=s;
    return flash->commit(proposed);
  }
  static bool commit(const blaze_credit::Snapshot& s,void* self){
    return static_cast<SlaveTxn*>(self)->write(s);
  }
};
struct MasterTxn {
  Flash* flash;
  bool write(const blaze_credit::MasterPending& s){
    Record proposed=flash->current.snapshot;
    proposed.master=s;
    return flash->commit(proposed);
  }
  static bool commit(const blaze_credit::MasterPending& s,void* self){
    return static_cast<MasterTxn*>(self)->write(s);
  }
};
void expect(Status actual,Status expected){assert(actual==expected);}
}
int main(){
  Flash d;
  d.recover();expect(d.current.status,Status::Absent);
  assert(d.init());
  assert(d.current.snapshot.generation==1);
  assert(d.current.snapshot.slave.remainingUnits==0);
  // Both initial slots are identical and valid.
  uint8_t initial[IMAGE_BYTES]={};
  memcpy(initial,d.slot[0],IMAGE_BYTES);
  assert(memcmp(initial,d.slot[1],IMAGE_BYTES)==0);
  // A swapped role, key or peer ID must fail before any money is accepted.
  d.expected.role=ROLE_MASTER;d.recover();expect(d.current.status,Status::Mismatch);
  d.expected.role=ROLE_SLAVE;d.expected.keyTag^=1;d.recover();
  expect(d.current.status,Status::Mismatch);
  d.expected.keyTag^=1;d.recover();expect(d.current.status,Status::Healthy);

  // Master records pending paid event BEFORE any send. Power cut before rename.
  d.expected.role=ROLE_MASTER;d.present[0]=d.present[1]=false;
  assert(d.init());
  MasterTxn mt{&d};auto master=d.current.snapshot.master;
  d.failWrite=true;
  assert(!blaze_credit::stage(master,60,&MasterTxn::commit,&mt));
  assert(master.lastIssued==0);d.failWrite=false;d.recover();
  expect(d.current.status,Status::Healthy);
  // Power cut after flush but BEFORE metadata rename: old snapshot wins.
  d.failRename=true;
  assert(!blaze_credit::stage(master,60,&MasterTxn::commit,&mt));
  d.failRename=false;d.recover();
  assert(d.current.snapshot.master.pendingSequence==0);
  // Successful durable stage.
  master=d.current.snapshot.master;
  assert(blaze_credit::stage(master,60,&MasterTxn::commit,&mt));
  assert(d.current.snapshot.master.pendingSequence==1);
  assert(d.current.snapshot.generation==2);
  assert(!blaze_credit::stage(master,120,&MasterTxn::commit,&mt));
  // Crash AFTER atomic rename, before caller sends packet/ACK.
  d.failPostRename=true;
  assert(!blaze_credit::settle(master,1,&MasterTxn::commit,&mt));
  d.failPostRename=false;d.recover();
  // Flash had settled even though call reported failure; reboot must inspect.
  assert(d.current.snapshot.master.pendingSequence==0);
  assert(d.current.snapshot.master.lastIssued==1);
  assert(!d.commit(d.current.snapshot)==false || d.current.status==Status::Healthy);

  // Separate Slave image: receipt dedupe + paid units in SAME record.
  Flash slave;
  assert(slave.init());
  SlaveTxn st{&slave};
  auto snapshot=slave.current.snapshot.slave;
  const blaze_credit::Event first={slave.expected.peer,1,90};
  slave.failRename=true;
  assert(blaze_credit::apply(snapshot,first,&SlaveTxn::commit,&st)==
         blaze_credit::Outcome::NotDurable);
  slave.failRename=false;slave.recover();
  assert(slave.current.snapshot.slave.lastSequence==0);
  assert(blaze_credit::apply(snapshot,first,&SlaveTxn::commit,&st)==
         blaze_credit::Outcome::Applied);
  assert(slave.current.snapshot.slave.remainingUnits==9000000ULL);
  assert(slave.current.snapshot.slave.lastSequence==1);
  assert(slave.current.snapshot.slave.paidEventCount==1);
  // Simulated reboot and lost ACK: retry SAME event cannot double grant.
  slave.recover();snapshot=slave.current.snapshot.slave;
  assert(blaze_credit::apply(snapshot,first,&SlaveTxn::commit,&st)==
         blaze_credit::Outcome::Duplicate);
  assert(slave.current.snapshot.slave.remainingUnits==9000000ULL);
  assert(slave.current.snapshot.slave.paidEventCount==1);

  // Post-rename crash must be re-read. Caller MUST fail-stop, not retry.
  const blaze_credit::Event second={slave.expected.peer,2,30};
  slave.failPostRename=true;
  assert(blaze_credit::apply(snapshot,second,&SlaveTxn::commit,&st)==
         blaze_credit::Outcome::NotDurable);
  slave.failPostRename=false;slave.recover();
  assert(slave.current.snapshot.slave.lastSequence==2);
  assert(slave.current.snapshot.slave.remainingUnits==12000000ULL);
  snapshot=slave.current.snapshot.slave;
  assert(blaze_credit::apply(snapshot,second,&SlaveTxn::commit,&st)==
         blaze_credit::Outcome::Duplicate);
  assert(slave.current.snapshot.slave.remainingUnits==12000000ULL);
  assert(blaze_credit::apply(snapshot,{slave.expected.peer,4,10},
                              &SlaveTxn::commit,&st)==
         blaze_credit::Outcome::OutOfOrder);
  assert(blaze_credit::apply(snapshot,{0x22222222,3,10},
                              &SlaveTxn::commit,&st)==
         blaze_credit::Outcome::WrongIssuer);

  // Invalid headers, checksum, two conflicting same generations, stale slots.
  Flash damaged;
  assert(damaged.init());
  damaged.slot[0][17]^=1;
  damaged.recover();expect(damaged.current.status,Status::Degraded);
  assert(!damaged.commit(damaged.current.snapshot));
  assert(damaged.init()==false); // never auto-reinitialize corrupted paid state
  Flash missing;assert(missing.init());
  missing.present[1]=false;missing.recover();
  expect(missing.current.status,Status::Degraded);
  Flash conflict;assert(conflict.init());
  Record changed=conflict.current.snapshot;
  changed.slave.remainingUnits=100000ULL;
  uint8_t alternate[IMAGE_BYTES]={};
  assert(encode(changed,alternate));
  memcpy(conflict.slot[1],alternate,IMAGE_BYTES);
  conflict.recover();expect(conflict.current.status,Status::Degraded);
  Flash stale;assert(stale.init());
  Record jump=stale.current.snapshot;jump.generation=4;
  uint8_t farAhead[IMAGE_BYTES]={};assert(encode(jump,farAhead));
  memcpy(stale.slot[1],farAhead,IMAGE_BYTES);
  stale.recover();expect(stale.current.status,Status::Degraded);
  // Host/ESP encoding agreement: no struct memory-image ambiguity.
  Record roundTrip={};
  assert(decode(initial,sizeof(initial),roundTrip));
  assert(roundTrip.generation==1&&roundTrip.bind.owner==0xAABBCCDD);
  uint8_t buf[IMAGE_BYTES]={};assert(encode(roundTrip,buf));
  assert(memcmp(buf,initial,IMAGE_BYTES)==0);
  assert(!decode(initial,sizeof(initial)-1,roundTrip));

  puts("PASS: 2-slot canonical images, journal generation, crash before/after rename, ACK loss, dedupe, wrong issuer and degraded fail-closed recovery");
  return 0;
}
