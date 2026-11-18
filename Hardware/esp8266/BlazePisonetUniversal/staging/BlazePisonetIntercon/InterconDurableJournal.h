#pragma once
// BLAZE INTERCON V1.8 — laboratory durable event/balance snapshot journal.
//
// This is a conservative two-slot, one-record-per-slot store: each successful
// commit contains BOTH the remote credit deduplication sequence AND the
// canonical paid-time balance in a single checksummed image. The Master uses
// the same format for its single unacknowledged coin event.
//
// IMPORTANT: The deployed V1.5 timer still persists time in EEPROM. The
// journal is intentionally NOT used to grant live credits or replay PWR_SW.
// Boot must not automatically reinitialize a missing/corrupt paid journal.
// A torn/invalid slot makes the store UNTRUSTED, even if the other slot is
// readable: falling back could silently roll back an acknowledged credit.
//
// Portable C++11; no Arduino, FS, networking, or hardware dependencies.
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "InterconCreditLedger.h"

namespace blaze_durable {

static const size_t RECORD_BYTES=76;
static const uint16_t VERSION=1;
static const uint32_t MAGIC=0x424C4A38UL; // "BLJ8" encoded little-endian

enum class Role : uint8_t { Master=1, Slave=2 };
enum class Load : uint8_t {
  Ready, Missing, Corrupt, BindingMismatch, IoError
};

struct Record {
  Role role;
  uint64_t generation;
  uint32_t localChip;
  uint32_t peerChip;
  blaze_credit::MasterPending master;
  blaze_credit::Snapshot slave;
};

// IO contract: the slot is absent, present and readable (with its actual
// byte count), or inaccessible. writeSlot must close/flush its handle before
// returning; a false return can STILL mean the new record hit flash, so
// caller must mark its session uncertain and reconcile on reboot.
enum class Read : uint8_t { Missing, Present, Error };
struct Storage {
  virtual ~Storage() {}
  virtual Read readSlot(uint8_t slot,uint8_t* bytes,size_t max,size_t& count)=0;
  virtual bool writeSlot(uint8_t slot,const uint8_t* bytes,size_t count)=0;
};

inline void put16(uint8_t* b,size_t o,uint16_t v) {
  for(size_t i=0;i<2;i++)b[o+i]=(uint8_t)(v>>(8*i));
}
inline void put32(uint8_t* b,size_t o,uint32_t v) {
  for(size_t i=0;i<4;i++)b[o+i]=(uint8_t)(v>>(8*i));
}
inline void put64(uint8_t* b,size_t o,uint64_t v) {
  for(size_t i=0;i<8;i++)b[o+i]=(uint8_t)(v>>(8*i));
}
inline uint16_t get16(const uint8_t* b,size_t o) {
  uint16_t v=0;for(size_t i=0;i<2;i++)v|=(uint16_t)b[o+i]<<(8*i);return v;
}
inline uint32_t get32(const uint8_t* b,size_t o) {
  uint32_t v=0;for(size_t i=0;i<4;i++)v|=(uint32_t)b[o+i]<<(8*i);return v;
}
inline uint64_t get64(const uint8_t* b,size_t o) {
  uint64_t v=0;for(size_t i=0;i<8;i++)v|=(uint64_t)b[o+i]<<(8*i);return v;
}
inline uint32_t crc32(const uint8_t* bytes,size_t length) {
  uint32_t crc=0xFFFFFFFFUL;
  for(size_t i=0;i<length;i++) {
    crc^=bytes[i];
    for(uint8_t k=0;k<8;k++)crc=(crc>>1)^((crc&1U)?0xEDB88320UL:0);
  }
  return ~crc;
}
inline bool valid(const Record& r) {
  if(!r.generation||!r.localChip||!r.peerChip||
     r.localChip==r.peerChip)return false;
  if(r.role==Role::Slave) {
    return r.slave.authorizedIssuer==r.peerChip &&
           r.slave.remainingUnits<=blaze_credit::MAX_UNITS &&
           (!r.slave.lastSequence || r.slave.lastSeconds>0) &&
           (!r.slave.paidEventCount || r.slave.lastSequence>0) &&
           !r.master.lastIssued && !r.master.pendingSequence &&
           !r.master.pendingSeconds;
  }
  if(r.role==Role::Master) {
    return r.master.pendingSequence<=r.master.lastIssued &&
           ((r.master.pendingSequence==0 && r.master.pendingSeconds==0)||
            (r.master.pendingSequence==r.master.lastIssued &&
             r.master.pendingSeconds>0)) &&
           !r.slave.authorizedIssuer && !r.slave.lastSequence &&
           !r.slave.remainingUnits && !r.slave.paidEventCount &&
           !r.slave.lastSeconds;
  }
  return false;
}
inline bool serialize(const Record& r,uint8_t out[RECORD_BYTES]) {
  if(!valid(r))return false;
  memset(out,0,RECORD_BYTES);
  put32(out,0,MAGIC);put16(out,4,VERSION);
  out[6]=(uint8_t)r.role;
  out[7]=0;
  put64(out,8,r.generation);
  put32(out,16,r.localChip);put32(out,20,r.peerChip);
  put64(out,24,r.master.lastIssued);
  put64(out,32,r.master.pendingSequence);
  put16(out,40,r.master.pendingSeconds);
  // [42:43] reserved = zero
  put32(out,44,r.slave.authorizedIssuer);
  put64(out,48,r.slave.lastSequence);
  put64(out,56,r.slave.remainingUnits);
  put32(out,64,r.slave.paidEventCount);
  put16(out,68,r.slave.lastSeconds);
  // [70:71] reserved = zero
  put32(out,72,crc32(out,72));
  return true;
}
inline bool deserialize(const uint8_t* bytes,size_t n,Record& out) {
  if(!bytes||n!=RECORD_BYTES||
     get32(bytes,0)!=MAGIC||get16(bytes,4)!=VERSION||
     bytes[7]!=0||bytes[42]!=0||bytes[43]!=0||
     bytes[70]!=0||bytes[71]!=0||
     get32(bytes,72)!=crc32(bytes,72))return false;
  Record r={};
  r.role=(Role)bytes[6];r.generation=get64(bytes,8);
  r.localChip=get32(bytes,16);r.peerChip=get32(bytes,20);
  r.master.lastIssued=get64(bytes,24);
  r.master.pendingSequence=get64(bytes,32);
  r.master.pendingSeconds=get16(bytes,40);
  r.slave.authorizedIssuer=get32(bytes,44);
  r.slave.lastSequence=get64(bytes,48);
  r.slave.remainingUnits=get64(bytes,56);
  r.slave.paidEventCount=get32(bytes,64);
  r.slave.lastSeconds=get16(bytes,68);
  if(!valid(r))return false;
  out=r;return true;
}

class Journal {
  Storage& io_;
  Record current_={};
  uint8_t active_=0;
  bool ready_=false;
  Load last_=Load::Missing;

  bool commit(const Record& candidate) {
    if(!ready_||!valid(candidate)||current_.generation==UINT64_MAX||
       candidate.generation!=current_.generation+1 ||
       candidate.role!=current_.role||
       candidate.localChip!=current_.localChip||
       candidate.peerChip!=current_.peerChip)return false;
    const uint8_t target=(uint8_t)(active_^1U);
    uint8_t encoded[RECORD_BYTES]={};
    if(!serialize(candidate,encoded))return false;
    if(!io_.writeSlot(target,encoded,RECORD_BYTES)) {
      ready_=false;last_=Load::IoError;return false;
    }
    uint8_t verify[RECORD_BYTES]={};
    size_t n=0;
    if(io_.readSlot(target,verify,RECORD_BYTES,n)!=Read::Present ||
       n!=RECORD_BYTES||memcmp(encoded,verify,RECORD_BYTES)!=0){
      ready_=false;last_=Load::IoError;return false;
    }
    current_=candidate;active_=target;last_=Load::Ready;return true;
  }
public:
  explicit Journal(Storage& io):io_(io){}
  bool ready() const {return ready_;}
  Load status() const {return last_;}
  const Record& record() const {return current_;}
  Load load(Role role,uint32_t localChip,uint32_t peerChip) {
    ready_=false;memset(&current_,0,sizeof(current_));
    if((role!=Role::Master&&role!=Role::Slave)||
       !localChip||!peerChip||localChip==peerChip)
      return last_=Load::BindingMismatch;
    Record found[2]={};
    bool present[2]={false,false};
    for(uint8_t i=0;i<2;i++){
      uint8_t b[RECORD_BYTES]={};
      size_t n=0;
      Read result=io_.readSlot(i,b,RECORD_BYTES,n);
      if(result==Read::Error)return last_=Load::IoError;
      if(result==Read::Missing)continue;
      if(!deserialize(b,n,found[i]))return last_=Load::Corrupt;
      if(found[i].role!=role||found[i].localChip!=localChip||
         found[i].peerChip!=peerChip)return last_=Load::BindingMismatch;
      present[i]=true;
    }
    if(!present[0]&&!present[1])return last_=Load::Missing;
    // Only a fresh generation-1 journal may legitimately have one slot.
    // A missing slot after an acknowledged later commit can mean rollback.
    if(present[0]!=present[1] &&
       found[present[0]?0:1].generation!=1)return last_=Load::Corrupt;
    if(present[0]&&present[1]){
      const uint64_t a=found[0].generation,b=found[1].generation;
      if(a==b || (a>b && a-b!=1) || (b>a && b-a!=1))
        return last_=Load::Corrupt;
      active_=(a>b)?0:1;
    } else active_=present[0]?0:1;
    current_=found[active_];
    ready_=true;return last_=Load::Ready;
  }
  // Only an out-of-band, paid-balance-reconciled maintenance action may call
  // initialize(), and only on an EMPTY journal. The production sketch does
  // not expose such an action.
  bool initialize(Role role,uint32_t local,uint32_t peer,
                  uint64_t existingBalance=0) {
    if(existingBalance>blaze_credit::MAX_UNITS ||
       load(role,local,peer)!=Load::Missing)return false;
    Record first={};
    first.role=role;first.localChip=local;first.peerChip=peer;
    first.generation=1;
    if(role==Role::Slave){
      first.slave.authorizedIssuer=peer;
      first.slave.remainingUnits=existingBalance;
    }
    uint8_t buf[RECORD_BYTES]={};
    if(!serialize(first,buf)||!io_.writeSlot(0,buf,RECORD_BYTES))
      return last_=Load::IoError,false;
    size_t n=0;uint8_t verify[RECORD_BYTES]={};
    if(io_.readSlot(0,verify,RECORD_BYTES,n)!=Read::Present ||
       n!=RECORD_BYTES||memcmp(buf,verify,RECORD_BYTES)!=0)
      return last_=Load::IoError,false;
    active_=0;current_=first;ready_=true;last_=Load::Ready;return true;
  }
  blaze_credit::Outcome applySlave(const blaze_credit::Event& event){
    if(!ready_||current_.role!=Role::Slave)
      return blaze_credit::Outcome::NotDurable;
    Record proposal=current_;
    const blaze_credit::Outcome decision=
      blaze_credit::prepare(current_.slave,event,proposal.slave);
    if(decision!=blaze_credit::Outcome::Applied)return decision;
    proposal.generation++;
    return commit(proposal)?blaze_credit::Outcome::Applied:
                           blaze_credit::Outcome::NotDurable;
  }
  bool stageMaster(uint16_t seconds){
    if(!ready_||current_.role!=Role::Master ||
       current_.master.pendingSequence||
       current_.master.lastIssued==UINT64_MAX||!seconds)return false;
    Record proposal=current_;
    proposal.master.lastIssued++;
    proposal.master.pendingSequence=proposal.master.lastIssued;
    proposal.master.pendingSeconds=seconds;
    proposal.generation++;
    return commit(proposal);
  }
  bool settleMaster(uint64_t acked){
    if(!ready_||current_.role!=Role::Master||!acked||
       acked!=current_.master.pendingSequence)return false;
    Record proposal=current_;
    proposal.master.pendingSequence=0;
    proposal.master.pendingSeconds=0;
    proposal.generation++;
    return commit(proposal);
  }
  bool checkpointRemaining(uint64_t remainingUnits){
    if(!ready_||current_.role!=Role::Slave ||
       remainingUnits>current_.slave.remainingUnits)return false;
    if(remainingUnits==current_.slave.remainingUnits)return true;
    Record proposal=current_;
    proposal.slave.remainingUnits=remainingUnits;
    proposal.generation++;
    return commit(proposal);
  }
};
} // namespace blaze_durable
