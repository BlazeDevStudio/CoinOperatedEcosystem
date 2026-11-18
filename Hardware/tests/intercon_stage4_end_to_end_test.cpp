// Stage 4 portable end-to-end financial integration test.
// Uses actual canonical HMAC wire codec + persistent Master/Slave journal
// algorithms. Emulates two flash slots and power-cut boundaries. Does NOT
// replace physical ESP8266 / real coin acceptor acceptance tests.
#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconSecureWire.h"
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconJournalCodec.h"
namespace b=blaze_credit;
namespace j=blaze_journal;
constexpr uint32_t MASTER_ID=0x0048A5D1, SLAVE_ID=0x00ACB209;
uint8_t KEY[32]={};
struct Node {
  j::Binding binding={};
  uint8_t slots[2][j::IMAGE_BYTES]={};
  bool present[2]={false,false};
  j::Recovered current={};
  bool failBeforeRename=false;
  bool failAfterRename=false;
  bool initialize(uint32_t owner,uint32_t peer,uint32_t role) {
    binding.owner=owner;binding.peer=peer;binding.role=role;
    uint8_t mac[32]={};
    static const char label[]="BLZJ-PAIR-BIND-v1";
    if(!blaze_peer::hmacSha256(KEY,label,sizeof(label)-1,mac))return false;
    memcpy(binding.keyTag,mac,16);
    j::Record initial={};
    initial.bind=binding;initial.generation=1;
    initial.slave.authorizedIssuer=peer;
    uint8_t image[j::IMAGE_BYTES]={};
    if(!j::encode(initial,image))return false;
    memcpy(slots[0],image,sizeof(image));
    memcpy(slots[1],image,sizeof(image));
    present[0]=present[1]=true;
    reboot();
    return current.status==j::Status::Healthy;
  }
  void reboot(){
    current=j::inspect(present[0],slots[0],present[1],slots[1],binding);
  }
  bool commit(const j::Record& requested){
    if(current.status!=j::Status::Healthy)return false;
    j::Record next={};uint8_t target=0;
    if(!j::next(current,requested,next,target))return false;
    uint8_t image[j::IMAGE_BYTES]={};
    if(!j::encode(next,image) || failBeforeRename)return false;
    memcpy(slots[target],image,sizeof(image)); // atomic file rename boundary
    present[target]=true;
    if(failAfterRename)return false; // new bytes survive crash, RAM stale
    reboot();
    return current.status==j::Status::Healthy &&
           current.snapshot.generation==next.generation;
  }
};
bool persistMaster(const b::MasterPending& changed,void* context){
  auto& master=*static_cast<Node*>(context);
  j::Record rec=master.current.snapshot;
  rec.master=changed;
  return master.commit(rec);
}
bool persistSlave(const b::Snapshot& changed,void* context){
  auto& slave=*static_cast<Node*>(context);
  j::Record rec=slave.current.snapshot;
  rec.slave=changed;
  return slave.commit(rec);
}
size_t signedFrame(char kind[5],uint32_t sender,uint32_t target,
                   uint64_t seq,uint16_t seconds,char (&wire)[blaze_peer::MAX_WIRE]){
  blaze_peer::Frame f={};
  memcpy(f.kind,kind,5);
  f.source=sender;f.destination=target;
  f.eventHigh=(uint32_t)(seq>>32);
  f.eventLow=(uint32_t)seq;f.units=seconds;
  return blaze_peer::encode(f,KEY,wire);
}
bool deliverCredit(Node& slave,const char* wire,size_t n,uint64_t activeUnits,
                   bool& accepted,bool& ackAllowed) {
  accepted=false;ackAllowed=false;
  blaze_peer::Frame packet={};
  if(!blaze_peer::decode(wire,n,KEY,MASTER_ID,SLAVE_ID,packet))return false;
  if(memcmp(packet.kind,"CRED",4)!=0 || !packet.units ||
     slave.current.status!=j::Status::Healthy)return false;
  b::Snapshot snap=slave.current.snapshot.slave;
  snap.remainingUnits=activeUnits; // settle RAM elapsed debit in same commit
  const uint64_t seq=((uint64_t)packet.eventHigh<<32)|packet.eventLow;
  b::Event event={packet.source,seq,packet.units};
  b::Outcome o=b::apply(snap,event,persistSlave,&slave);
  if(o==b::Outcome::Applied){
    accepted=true;ackAllowed=true;
  }else if(o==b::Outcome::Duplicate){
    ackAllowed=seq==slave.current.snapshot.slave.lastSequence &&
               packet.units==slave.current.snapshot.slave.lastSeconds;
  }
  return true;
}
int main(){
  for(int i=0;i<32;i++)KEY[i]=(uint8_t)(i+3);
  Node master,slave;
  assert(master.initialize(MASTER_ID,SLAVE_ID,j::ROLE_MASTER));
  assert(slave.initialize(SLAVE_ID,MASTER_ID,j::ROLE_SLAVE));
  b::MasterPending pending=master.current.snapshot.master;
  assert(b::stage(pending,60,persistMaster,&master));
  assert(master.current.snapshot.master.pendingSequence==1);

  char credit[blaze_peer::MAX_WIRE]={};
  char creditKind[5]="CRED";
  size_t n=signedFrame(creditKind,MASTER_ID,SLAVE_ID,1,60,credit);
  assert(n>0);
  bool accepted=false,ack=false;
  assert(deliverCredit(slave,credit,n,0,accepted,ack));
  assert(accepted&&ack);
  assert(slave.current.snapshot.slave.lastSequence==1);
  assert(slave.current.snapshot.slave.remainingUnits==6000000ULL);
  assert(slave.current.snapshot.slave.paidEventCount==1);
  // ACK was lost; both nodes restart, Master resends original transaction.
  master.reboot();slave.reboot();
  assert(master.current.snapshot.master.pendingSequence==1);
  assert(deliverCredit(slave,credit,n,6000000ULL,accepted,ack));
  assert(!accepted&&ack);
  assert(slave.current.snapshot.slave.paidEventCount==1);
  char ackWire[blaze_peer::MAX_WIRE]={},ackKind[5]="ACKN";
  size_t an=signedFrame(ackKind,SLAVE_ID,MASTER_ID,1,0,ackWire);
  blaze_peer::Frame verifiedAck={};
  assert(blaze_peer::decode(ackWire,an,KEY,SLAVE_ID,MASTER_ID,verifiedAck));
  assert(!b::settle(pending,2,persistMaster,&master));
  pending=master.current.snapshot.master;
  assert(b::settle(pending,1,persistMaster,&master));
  assert(master.current.snapshot.master.pendingSequence==0);

  // Paid countdown consumes 20 seconds. The receipt and balance checkpoint
  // are updated together; the old EEPROM state is irrelevant to recovery.
  j::Record checkpoint=slave.current.snapshot;
  checkpoint.slave.remainingUnits=4000000ULL;
  assert(slave.commit(checkpoint));
  slave.reboot();
  assert(slave.current.snapshot.slave.remainingUnits==4000000ULL);
  assert(slave.current.snapshot.slave.lastSequence==1);

  // Stage the next physical coin event. Failure BEFORE flash rename must not
  // send CREDIT or open coin slot: no durable pending record exists yet.
  pending=master.current.snapshot.master;
  master.failBeforeRename=true;
  assert(!b::stage(pending,30,persistMaster,&master));
  master.failBeforeRename=false;
  master.reboot();
  assert(master.current.snapshot.master.pendingSequence==0);
  assert(b::stage(pending,30,persistMaster,&master));

  char second[blaze_peer::MAX_WIRE]={};
  n=signedFrame(creditKind,MASTER_ID,SLAVE_ID,2,30,second);
  // Slave power cut BEFORE rename: no credit and no receipt ACK.
  slave.failBeforeRename=true;
  assert(deliverCredit(slave,second,n,4000000ULL,accepted,ack));
  assert(!accepted&&!ack);
  slave.failBeforeRename=false;slave.reboot();
  assert(slave.current.snapshot.slave.lastSequence==1);
  // Cut AFTER rename, before ACK: durable remote time exists, but handler
  // must fail closed and learn the outcome on reboot.
  slave.failAfterRename=true;
  assert(deliverCredit(slave,second,n,4000000ULL,accepted,ack));
  assert(!accepted&&!ack);
  slave.failAfterRename=false;slave.reboot();
  assert(slave.current.snapshot.slave.lastSequence==2);
  assert(slave.current.snapshot.slave.remainingUnits==7000000ULL);
  assert(slave.current.snapshot.slave.paidEventCount==2);
  assert(deliverCredit(slave,second,n,7000000ULL,accepted,ack));
  assert(!accepted&&ack); // retry is duplicate; no extra paid time
  // Auth cannot be removed: wrong target and tampered messages rejected.
  blaze_peer::Frame rejected={};
  assert(!blaze_peer::decode(second,n,KEY,MASTER_ID,MASTER_ID,rejected));
  char tamper[blaze_peer::MAX_WIRE]={};memcpy(tamper,second,n);
  tamper[n-1]=(tamper[n-1]=='A'?'B':'A');
  assert(!blaze_peer::decode(tamper,n,KEY,MASTER_ID,SLAVE_ID,rejected));
  // Admin manual adjustment is durable WITHOUT incrementing coin receipts.
  j::Record manual=slave.current.snapshot;
  manual.slave.remainingUnits=12000000ULL;
  assert(slave.commit(manual));
  slave.reboot();
  assert(slave.current.snapshot.slave.remainingUnits==12000000ULL);
  assert(slave.current.snapshot.slave.lastSequence==2);
  assert(slave.current.snapshot.slave.paidEventCount==2);
  // Expiry writes zero in the same journal before requesting PC shutdown.
  j::Record expires=slave.current.snapshot;
  expires.slave.remainingUnits=0;
  assert(slave.commit(expires));slave.reboot();
  assert(slave.current.snapshot.slave.remainingUnits==0);
  assert(slave.current.snapshot.slave.lastSequence==2);
  // Missing / torn journal slot is never accepted as authoritative.
  slave.slots[0][26]^=1;slave.reboot();
  assert(slave.current.status==j::Status::Degraded);
  assert(!slave.commit(expires));
  puts("PASS: signed Master staging, Slave atomic time+receipt, restart, ACK loss, two crash boundaries, replay, admin adjustment, expiry, corrupt-flash lock");
}
