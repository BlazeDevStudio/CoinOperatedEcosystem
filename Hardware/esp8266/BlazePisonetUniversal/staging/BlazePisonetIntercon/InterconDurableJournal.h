#pragma once
// BLAZE INTERCON V1.8 — fail-closed two-slot, versioned credit journal.
// Portable, deterministic bytes. No remote credit can be applied merely by
// including this file. The firmware does not authorize paid Master/Slave mode.
//
// Storage MUST atomically write the alternate slot via temp + rename while
// retaining the current valid slot. If an I/O outcome is uncertain the journal
// locks until recovery; never ACK a paid event on uncertain durability.
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "InterconCreditLedger.h"

namespace blaze_journal {
static const uint32_t MAGIC = 0x4A434942UL; // BI CJ as little-endian bytes
static const uint16_t VERSION = 1;
static const size_t RECORD_SIZE = 64;
enum class Kind : uint16_t { Master=1, Slave=2 };
enum class Status : uint8_t {
  Empty, Ready, Degraded, Corrupt, IoError, WrongKind, Uncertain
};
inline const char* statusName(Status status) {
  switch(status){
    case Status::Empty:return "NOT_INITIALIZED";
    case Status::Ready:return "READY";
    case Status::Degraded:return "DEGRADED_LOCKED";
    case Status::Corrupt:return "CORRUPT_LOCKED";
    case Status::IoError:return "IO_ERROR_LOCKED";
    case Status::WrongKind:return "WRONG_ROLE_LOCKED";
    case Status::Uncertain:return "UNCERTAIN_LOCKED";
  }
  return "UNKNOWN_LOCKED";
}
struct Payload {
  uint32_t issuer;         // Master: own chip; Slave: authorized paired Master
  uint64_t sequence;       // Last issued or received monotonic sequence
  uint64_t remainingUnits; // 0.01-ms units, authoritative only after full rollout
  uint32_t paidCount;      // Master source count or Slave received count
  uint16_t lastSeconds;
  uint16_t pendingSeconds;
  uint64_t pendingSequence;
};
struct Record {
  Kind kind;
  uint64_t generation;
  Payload p;
};
// read() must set actualLen=0 for a non-existent slot, and return true.
// A slot with invalid size is reported as valid I/O with actualLen != 64.
// write() atomically replaces only alternate slot; do not touch active slot.
struct IO {
  bool (*read)(void*,char slot,uint8_t out[RECORD_SIZE],size_t& actualLen);
  bool (*write)(void*,char slot,const uint8_t data[RECORD_SIZE]);
  void* context;
};
inline void u16(uint8_t*b,uint16_t n){
  b[0]=(uint8_t)n;b[1]=(uint8_t)(n>>8);
}
inline void u32(uint8_t*b,uint32_t n){
  for(int i=0;i<4;i++)b[i]=(uint8_t)(n>>(i*8));
}
inline void u64(uint8_t*b,uint64_t n){
  for(int i=0;i<8;i++)b[i]=(uint8_t)(n>>(i*8));
}
inline uint16_t r16(const uint8_t*b){return (uint16_t)b[0]|((uint16_t)b[1]<<8);}
inline uint32_t r32(const uint8_t*b){
  uint32_t n=0;for(int i=3;i>=0;i--)n=(n<<8)|b[i];return n;
}
inline uint64_t r64(const uint8_t*b){
  uint64_t n=0;for(int i=7;i>=0;i--)n=(n<<8)|b[i];return n;
}
inline uint32_t crc32(const uint8_t*b,size_t n){
  uint32_t crc=0xffffffffUL;
  for(size_t i=0;i<n;i++){
    crc^=b[i];
    for(uint8_t j=0;j<8;j++)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);
  }
  return ~crc;
}
inline bool valid(const Record&r){
  if(r.kind!=Kind::Master && r.kind!=Kind::Slave)return false;
  if(r.generation==0 || !r.p.issuer ||
     r.p.remainingUnits>blaze_credit::MAX_UNITS)return false;
  if(r.kind==Kind::Master){
    if((r.p.pendingSequence==0)!=(r.p.pendingSeconds==0))return false;
    if(r.p.pendingSequence && r.p.pendingSequence!=r.p.sequence)return false;
    if(r.p.lastSeconds!=0)return false;
  }else{
    if(r.p.pendingSequence!=0 || r.p.pendingSeconds!=0)return false;
    if(r.p.sequence==0 && (r.p.paidCount!=0||r.p.lastSeconds!=0))return false;
    if(r.p.sequence>0 && (r.p.paidCount==0||r.p.lastSeconds==0))return false;
  }
  return true;
}
inline bool serialize(const Record&r,uint8_t out[RECORD_SIZE]){
  if(!valid(r))return false;
  memset(out,0,RECORD_SIZE);
  u32(out+0,MAGIC);u16(out+4,VERSION);u16(out+6,(uint16_t)r.kind);
  u64(out+8,r.generation);
  u32(out+16,r.p.issuer);
  u64(out+20,r.p.sequence);
  u64(out+28,r.p.remainingUnits);
  u32(out+36,r.p.paidCount);
  u16(out+40,r.p.lastSeconds);
  u16(out+42,r.p.pendingSeconds);
  u64(out+44,r.p.pendingSequence);
  // bytes 52-59 MUST be zero; reserved for future protocol version
  u32(out+60,crc32(out,60));
  return true;
}
inline bool deserialize(const uint8_t in[RECORD_SIZE],Record& r){
  if(r32(in+0)!=MAGIC||r16(in+4)!=VERSION||
     crc32(in,60)!=r32(in+60)||r32(in+52)!=0||r32(in+56)!=0)return false;
  Record candidate={};
  candidate.kind=(Kind)r16(in+6);candidate.generation=r64(in+8);
  candidate.p.issuer=r32(in+16);
  candidate.p.sequence=r64(in+20);
  candidate.p.remainingUnits=r64(in+28);
  candidate.p.paidCount=r32(in+36);
  candidate.p.lastSeconds=r16(in+40);
  candidate.p.pendingSeconds=r16(in+42);
  candidate.p.pendingSequence=r64(in+44);
  if(!valid(candidate))return false;
  r=candidate;return true;
}
class Journal {
  IO io={};
  Kind expected=Kind::Slave;
  Record current={};
  Status state=Status::Empty;
  char active='B';
  bool hasCurrent=false;
public:
  explicit Journal(IO adapter,Kind kind):io(adapter),expected(kind){}
  Status status()const{return state;}
  bool ready()const{return state==Status::Ready;}
  bool hasRecord()const{return hasCurrent;}
  const Record& record()const{return current;}
  char activeSlot()const{return active;}
  Status recover(){
    state=Status::IoError;hasCurrent=false;
    if(!io.read||!io.write)return state;
    uint8_t a[RECORD_SIZE]={},b[RECORD_SIZE]={};
    size_t alen=0,blen=0;
    if(!io.read(io.context,'A',a,alen)||!io.read(io.context,'B',b,blen))return state;
    if(alen==0&&blen==0){state=Status::Empty;return state;}
    Record ra={},rb={};
    const bool agood=alen==RECORD_SIZE&&deserialize(a,ra);
    const bool bgood=blen==RECORD_SIZE&&deserialize(b,rb);
    if(!agood&&!bgood){state=Status::Corrupt;return state;}
    if(agood&&bgood&&ra.generation==rb.generation){
      // Equal generations with divergent payload are ambiguous; never guess.
      if(memcmp(a,b,RECORD_SIZE)!=0){state=Status::Corrupt;return state;}
    }
    const bool chooseA=agood&&(!bgood||ra.generation>=rb.generation);
    current=chooseA?ra:rb;active=chooseA?'A':'B';hasCurrent=true;
    if(current.kind!=expected){state=Status::WrongKind;return state;}
    // A torn or corrupt inactive slot indicates an unresolved write. Do not
    // silently roll back a paid credit without admin-led reconciliation.
    if((alen>0&&!agood)||(blen>0&&!bgood)){
      state=Status::Degraded;return state;
    }
    state=Status::Ready;return state;
  }
  bool initialize(const Payload& p){
    if(state!=Status::Empty)return false;
    Record initial={expected,1,p};
    uint8_t bytes[RECORD_SIZE]={};
    if(!serialize(initial,bytes)){state=Status::Corrupt;return false;}
    if(!io.write(io.context,'A',bytes)){state=Status::Uncertain;return false;}
    uint8_t verification[RECORD_SIZE]={};size_t length=0;
    if(!io.read(io.context,'A',verification,length)||
       length!=RECORD_SIZE||memcmp(bytes,verification,RECORD_SIZE)!=0){
      state=Status::Uncertain;return false;
    }
    current=initial;active='A';hasCurrent=true;state=Status::Ready;
    return true;
  }
  bool commit(const Record& proposed){
    if(!ready()||!hasCurrent||current.generation==UINT64_MAX ||
       proposed.kind!=expected)return false;
    Record target=proposed;
    target.generation=current.generation+1;
    uint8_t bytes[RECORD_SIZE]={};
    if(!serialize(target,bytes))return false;
    const char alternate=active=='A'?'B':'A';
    if(!io.write(io.context,alternate,bytes)){
      state=Status::Uncertain;return false;
    }
    uint8_t reread[RECORD_SIZE]={};size_t actual=0;
    if(!io.read(io.context,alternate,reread,actual)||
       actual!=RECORD_SIZE||memcmp(bytes,reread,RECORD_SIZE)!=0){
      state=Status::Uncertain;return false;
    }
    current=target;active=alternate;return true;
  }
};
// Callable by the EXISTING portable ledger; does not update timer unless
// the caller explicitly adopts the verified authoritative record.
inline bool commitSlaveSnapshot(const blaze_credit::Snapshot& next,void*opaque){
  Journal& store=*static_cast<Journal*>(opaque);
  if(!store.ready()||!store.hasRecord()||
     store.record().kind!=Kind::Slave||
     store.record().p.issuer!=next.authorizedIssuer)return false;
  Record updated=store.record();
  updated.p.sequence=next.lastSequence;
  updated.p.remainingUnits=next.remainingUnits;
  updated.p.paidCount=next.paidEventCount;
  updated.p.lastSeconds=next.lastSeconds;
  return store.commit(updated);
}
inline bool commitMasterPending(const blaze_credit::MasterPending& next,void*opaque){
  Journal& store=*static_cast<Journal*>(opaque);
  if(!store.ready()||!store.hasRecord()||store.record().kind!=Kind::Master)return false;
  Record updated=store.record();
  updated.p.sequence=next.lastIssued;
  updated.p.pendingSequence=next.pendingSequence;
  updated.p.pendingSeconds=next.pendingSeconds;
  return store.commit(updated);
}
} // namespace blaze_journal
