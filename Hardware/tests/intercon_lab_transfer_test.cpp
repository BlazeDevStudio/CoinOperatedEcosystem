// Real portable protocol + durable journal integration test.
// Simulates two independently persisted ESP8266 nodes without physical coins.
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconSecureWire.h"
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconDurableJournal.h"
using namespace blaze_peer;
using namespace blaze_credit;
using namespace blaze_journal;

struct Flash {
  struct Slot { bool exists=false; size_t len=0; uint8_t data[RECORD_SIZE]={}; } slots[2];
  bool failNext=false;
  bool tearNext=false;
  static int slotId(char name){ return name=='A'?0:name=='B'?1:-1; }
  static bool read(void*ctx,char name,uint8_t out[RECORD_SIZE],size_t&len){
    Flash& f=*static_cast<Flash*>(ctx);
    const int n=slotId(name);
    if(n<0)return false;
    len=f.slots[n].exists?f.slots[n].len:0;
    if(len==RECORD_SIZE)memcpy(out,f.slots[n].data,RECORD_SIZE);
    return true;
  }
  static bool write(void*ctx,char name,const uint8_t bytes[RECORD_SIZE]){
    Flash& f=*static_cast<Flash*>(ctx);
    const int n=slotId(name);
    if(n<0)return false;
    if(f.failNext){f.failNext=false;return false;}
    f.slots[n].exists=true;
    if(f.tearNext){f.tearNext=false;f.slots[n].len=15;return false;}
    f.slots[n].len=RECORD_SIZE;
    memcpy(f.slots[n].data,bytes,RECORD_SIZE);
    return true;
  }
  IO io(){return {&Flash::read,&Flash::write,this};}
};
static Snapshot snapshot(const Journal&j){
  const auto& p=j.record().p;
  return {p.issuer,p.sequence,p.remainingUnits,p.paidCount,p.lastSeconds};
}
static MasterPending masterState(const Journal&j){
  const auto& p=j.record().p;
  return {p.sequence,p.pendingSequence,p.pendingSeconds};
}
static Frame creditFrame(uint32_t master,uint32_t slave,MasterPending p){
  Frame f={};
  memcpy(f.kind,"CRED",5);
  f.source=master;f.destination=slave;
  f.eventHigh=(uint32_t)(p.pendingSequence>>32);
  f.eventLow=(uint32_t)p.pendingSequence;
  f.units=p.pendingSeconds;
  return f;
}
static uint64_t seq(const Frame&f){
  return ((uint64_t)f.eventHigh<<32)|(uint64_t)f.eventLow;
}
static Outcome receive(Journal&slave,const Frame&f){
  Snapshot state=snapshot(slave);
  return apply(state,{f.source,seq(f),f.units},commitSlaveSnapshot,&slave);
}
int main(){
  const uint32_t masterId=0xAABBCCDD,slaveId=0x12345678;
  uint8_t key[32]={};for(int i=0;i<32;i++)key[i]=(uint8_t)(i*7+1);
  Flash masterFlash={},slaveFlash={};
  Journal mj(masterFlash.io(),Kind::Master);
  Journal sj(slaveFlash.io(),Kind::Slave);
  assert(mj.recover()==Status::Empty&&sj.recover()==Status::Empty);
  Payload mp={};mp.issuer=masterId;
  Payload sp={};sp.issuer=masterId;
  assert(mj.initialize(mp)&&sj.initialize(sp));
  // Real staged/persisted Master transaction, no second event before ACK.
  MasterPending p=masterState(mj);
  assert(stage(p,60,commitMasterPending,&mj));
  assert(!stage(p,30,commitMasterPending,&mj));
  assert(mj.record().p.pendingSequence==1);
  Frame source=creditFrame(masterId,slaveId,p);
  char wire[MAX_WIRE]={};
  size_t bytes=encode(source,key,wire);
  assert(bytes>0);
  Frame accepted={};
  assert(decode(wire,bytes,key,masterId,slaveId,accepted));
  assert(receive(sj,accepted)==Outcome::Applied);
  assert(sj.record().p.sequence==1&&sj.record().p.paidCount==1);
  assert(sj.record().p.remainingUnits==6000000ULL);
  // Slave committed, ACK was lost, Master and Slave power-cycle.
  Journal masterReboot(masterFlash.io(),Kind::Master);
  Journal slaveReboot(slaveFlash.io(),Kind::Slave);
  assert(masterReboot.recover()==Status::Ready);
  assert(slaveReboot.recover()==Status::Ready);
  MasterPending resumed=masterState(masterReboot);
  Frame retry=creditFrame(masterId,slaveId,resumed);
  bytes=encode(retry,key,wire);
  assert(decode(wire,bytes,key,masterId,slaveId,accepted));
  assert(receive(slaveReboot,accepted)==Outcome::Duplicate);
  assert(slaveReboot.record().p.paidCount==1);
  // ACK is a separate signed message; accept only for pending same sequence.
  Frame ack={};
  memcpy(ack.kind,"ACKN",5);
  ack.source=slaveId;ack.destination=masterId;
  ack.eventHigh=retry.eventHigh;ack.eventLow=retry.eventLow;ack.units=0;
  bytes=encode(ack,key,wire);
  assert(bytes>0);
  Frame receivedAck={};
  assert(decode(wire,bytes,key,slaveId,masterId,receivedAck));
  assert(seq(receivedAck)==resumed.pendingSequence);
  assert(settle(resumed,seq(receivedAck),commitMasterPending,&masterReboot));
  assert(masterReboot.record().p.pendingSequence==0);
  assert(!settle(resumed,seq(receivedAck),commitMasterPending,&masterReboot));
  // Second credit after explicit settled ACK; 30 seconds.
  assert(stage(resumed,30,commitMasterPending,&masterReboot));
  Frame second=creditFrame(masterId,slaveId,resumed);
  bytes=encode(second,key,wire);
  assert(decode(wire,bytes,key,masterId,slaveId,accepted));
  assert(receive(slaveReboot,accepted)==Outcome::Applied);
  assert(slaveReboot.record().p.sequence==2);
  assert(slaveReboot.record().p.remainingUnits==9000000ULL);
  assert(slaveReboot.record().p.paidCount==2);
  // Signed but wrong-source/wrong-destination and tampered packets are rejected.
  assert(!decode(wire,bytes,key,slaveId,slaveId,accepted));
  assert(!decode(wire,bytes,key,masterId,masterId,accepted));
  char corrupt[MAX_WIRE]={};
  memcpy(corrupt,wire,bytes);corrupt[20]^=0x01;
  assert(!decode(corrupt,bytes,key,masterId,slaveId,accepted));
  uint8_t otherKey[32]={};
  assert(!decode(wire,bytes,otherKey,masterId,slaveId,accepted));
  // Persisted second event cannot be applied twice, even after reboot.
  Journal slave2(slaveFlash.io(),Kind::Slave);
  assert(slave2.recover()==Status::Ready);
  assert(receive(slave2,second)==Outcome::Duplicate);
  assert(receive(slave2,creditFrame(masterId,slaveId,{2,4,15}))==Outcome::OutOfOrder);
  // Failed flash commit MUST NOT ACK or advance local state.
  slaveFlash.failNext=true;
  Frame third=creditFrame(masterId,slaveId,{3,3,15});
  assert(receive(slave2,third)==Outcome::NotDurable);
  assert(slave2.status()==Status::Uncertain);
  assert(slave2.record().p.sequence==2);
  Journal recovered(slaveFlash.io(),Kind::Slave);
  assert(recovered.recover()==Status::Ready);
  assert(receive(recovered,third)==Outcome::Applied);
  // Torn flash write quarantines all future transactions.
  slaveFlash.tearNext=true;
  Frame fourth=creditFrame(masterId,slaveId,{4,4,15});
  assert(receive(recovered,fourth)==Outcome::NotDurable);
  Journal locked(slaveFlash.io(),Kind::Slave);
  assert(locked.recover()==Status::Degraded);
  assert(!locked.ready());
  assert(receive(locked,fourth)==Outcome::NotDurable);
  puts("PASS: signed Master -> durable Slave -> signed ACK; lost ACK, reboot, replay, corrupt, tear, fail closed");
}
