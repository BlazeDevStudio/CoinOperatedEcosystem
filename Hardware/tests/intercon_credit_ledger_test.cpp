#include <cassert>
#include <cstdio>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconCreditLedger.h"
using namespace blaze_credit;
struct DurableSlave { Snapshot saved;bool fail=false;uint32_t commits=0;};
bool commitSlave(const Snapshot& proposed,void* opaque){
  DurableSlave& d=*static_cast<DurableSlave*>(opaque);
  if(d.fail)return false;d.saved=proposed;d.commits++;return true;
}
struct DurableMaster { MasterPending saved;bool fail=false;uint32_t commits=0;};
bool commitMaster(const MasterPending& proposed,void* opaque){
  DurableMaster& d=*static_cast<DurableMaster*>(opaque);
  if(d.fail)return false;d.saved=proposed;d.commits++;return true;
}
int main(){
  DurableMaster md={};
  MasterPending master={};
  assert(stage(master,60,commitMaster,&md));
  assert(master.pendingSequence==1&&md.saved.pendingSequence==1);
  assert(!stage(master,30,commitMaster,&md)); // cannot overwrite unknown paid event
  DurableSlave sd={};
  Snapshot slave={};slave.authorizedIssuer=0xAABBCCDD;
  const Event first={0xAABBCCDD,master.pendingSequence,master.pendingSeconds};
  assert(apply(slave,first,commitSlave,&sd)==Outcome::Applied);
  assert(sd.saved.lastSequence==1&&sd.saved.remainingUnits==6000000ULL);
  assert(sd.commits==1&&slave.paidEventCount==1);
  // ACK is lost. Master reboots and retransmits same event.
  master=md.saved;
  assert(apply(slave,first,commitSlave,&sd)==Outcome::Duplicate);
  assert(sd.commits==1&&slave.remainingUnits==6000000ULL);
  assert(!settle(master,2,commitMaster,&md));
  assert(settle(master,1,commitMaster,&md));
  assert(master.pendingSequence==0&&md.saved.pendingSequence==0);
  // Slave reboot: reload durable record, still refuse replay.
  slave=sd.saved;
  assert(apply(slave,first,commitSlave,&sd)==Outcome::Duplicate);
  assert(apply(slave,{0xAABBCCDD,3,90},commitSlave,&sd)==Outcome::OutOfOrder);
  assert(apply(slave,{0x11223344,2,60},commitSlave,&sd)==Outcome::WrongIssuer);
  assert(stage(master,30,commitMaster,&md));
  sd.fail=true;
  const Event second={0xAABBCCDD,2,30};
  assert(apply(slave,second,commitSlave,&sd)==Outcome::NotDurable);
  assert(slave.lastSequence==1&&sd.saved.lastSequence==1);
  sd.fail=false;
  assert(apply(slave,second,commitSlave,&sd)==Outcome::Applied);
  assert(slave.lastSequence==2&&slave.remainingUnits==9000000ULL);
  assert(apply(slave,{0xAABBCCDD,2,999},commitSlave,&sd)==Outcome::Conflict);
  assert(apply(slave,second,commitSlave,&sd)==Outcome::Duplicate);
  slave.remainingUnits=MAX_UNITS-100000ULL;
  assert(apply(slave,{0xAABBCCDD,3,60},commitSlave,&sd)==Outcome::Overflow);
  DurableMaster failed={};failed.fail=true;
  MasterPending start={};
  assert(!stage(start,60,commitMaster,&failed)&&start.lastIssued==0);
  puts("PASS: applied once, lost ACK/retransmit, reboot, ordered sequence, fail-stop durable writes, overflow");
}
