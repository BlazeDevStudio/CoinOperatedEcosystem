#pragma once
// BLAZE INTERCON Stage 3: portable, canonical two-slot flash journal format.
// This file has no Arduino or filesystem dependencies and can be compiled with
// a native C++ compiler for deterministic power-fault tests.
//
// The record stores the Master pending-event state and the Slave dedupe key,
// paid-event count, and credit balance IN THE SAME atomic image. It is NOT
// automatically authoritative over the legacy V1.5 EEPROM timer.
//
// CRC-32 detects torn/corrupted images; it is NOT an authentication tag.
// Peer identity and key binding must be checked before using recovered state.
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "InterconCreditLedger.h"

namespace blaze_journal {
static const size_t IMAGE_BYTES=80;
static const uint32_t MAGIC=0x4A5A4C42UL; // "BLZJ" little endian
static const uint16_t VERSION=1;
static const uint32_t ROLE_MASTER=1, ROLE_SLAVE=2;
struct Binding {
  uint32_t owner;
  uint32_t peer;
  uint32_t keyTag; // HMAC-derived 32-bit fingerprint, not secret material
  uint32_t role;   // Master or Slave, never Standard
};
struct Record {
  Binding bind;
  uint64_t generation;
  blaze_credit::MasterPending master;
  blaze_credit::Snapshot slave;
};
enum class Status : uint8_t { Absent, Healthy, Degraded, Mismatch };
struct Recovered {
  Status status;
  Record snapshot;
  uint8_t newestSlot;
};
inline void w16(uint8_t* b,uint16_t n){
  b[0]=(uint8_t)n;b[1]=(uint8_t)(n>>8);
}
inline void w32(uint8_t* b,uint32_t n){
  for(uint8_t i=0;i<4;i++)b[i]=(uint8_t)(n>>(8*i));
}
inline void w64(uint8_t* b,uint64_t n){
  for(uint8_t i=0;i<8;i++)b[i]=(uint8_t)(n>>(8*i));
}
inline uint16_t r16(const uint8_t* b){
  return (uint16_t)b[0] | (uint16_t)((uint16_t)b[1]<<8);
}
inline uint32_t r32(const uint8_t* b){
  uint32_t n=0;for(uint8_t i=0;i<4;i++)n|=(uint32_t)b[i]<<(8*i);
  return n;
}
inline uint64_t r64(const uint8_t* b){
  uint64_t n=0;for(uint8_t i=0;i<8;i++)n|=(uint64_t)b[i]<<(8*i);
  return n;
}
inline uint32_t crc32(const uint8_t* bytes,size_t n){
  uint32_t c=0xFFFFFFFFUL;
  for(size_t i=0;i<n;i++){
    c^=bytes[i];
    for(uint8_t j=0;j<8;j++)c=(c>>1)^((c&1U)?0xEDB88320UL:0U);
  }
  return ~c;
}
inline bool valid(const Record& s){
  if(!s.generation || !s.bind.owner || !s.bind.peer ||
     s.bind.owner==s.bind.peer || !s.bind.keyTag ||
     (s.bind.role!=ROLE_MASTER && s.bind.role!=ROLE_SLAVE))return false;
  if(s.master.pendingSequence>s.master.lastIssued)return false;
  if(s.master.pendingSequence &&
     (s.master.pendingSequence!=s.master.lastIssued ||
      !s.master.pendingSeconds))return false;
  if(!s.master.pendingSequence && s.master.pendingSeconds)return false;
  if(s.slave.authorizedIssuer!=s.bind.peer ||
     s.slave.remainingUnits>blaze_credit::MAX_UNITS ||
     (s.slave.lastSequence==0 && (s.slave.lastSeconds ||
                                   s.slave.paidEventCount)) ||
     (s.slave.lastSequence!=0 &&
      (!s.slave.lastSeconds || !s.slave.paidEventCount)))return false;
  return true;
}
inline bool encode(const Record& s,uint8_t out[IMAGE_BYTES]){
  if(!valid(s))return false;
  memset(out,0,IMAGE_BYTES);
  w32(out+0,MAGIC);
  w16(out+4,VERSION);
  w16(out+6,0);
  w64(out+8,s.generation);
  w32(out+16,s.bind.owner);
  w32(out+20,s.bind.peer);
  w32(out+24,s.bind.keyTag);
  w32(out+28,s.bind.role);
  w64(out+32,s.master.lastIssued);
  w64(out+40,s.master.pendingSequence);
  w32(out+48,s.master.pendingSeconds);
  w64(out+52,s.slave.lastSequence);
  w64(out+60,s.slave.remainingUnits);
  w32(out+68,s.slave.paidEventCount);
  w32(out+72,s.slave.lastSeconds);
  w32(out+76,crc32(out,76));
  return true;
}
inline bool decode(const uint8_t* in,size_t len,Record& out){
  if(!in||len!=IMAGE_BYTES ||
     r32(in+0)!=MAGIC || r16(in+4)!=VERSION || r16(in+6)!=0 ||
     r32(in+76)!=crc32(in,76) ||
     r32(in+48)>UINT16_MAX || r32(in+72)>UINT16_MAX)return false;
  Record result={};
  result.generation=r64(in+8);
  result.bind.owner=r32(in+16);
  result.bind.peer=r32(in+20);
  result.bind.keyTag=r32(in+24);
  result.bind.role=r32(in+28);
  result.master.lastIssued=r64(in+32);
  result.master.pendingSequence=r64(in+40);
  result.master.pendingSeconds=(uint16_t)r32(in+48);
  result.slave.authorizedIssuer=result.bind.peer;
  result.slave.lastSequence=r64(in+52);
  result.slave.remainingUnits=r64(in+60);
  result.slave.paidEventCount=r32(in+68);
  result.slave.lastSeconds=(uint16_t)r32(in+72);
  if(!valid(result))return false;
  out=result;
  return true;
}
inline bool bindingMatches(const Binding& a,const Binding& b){
  return a.owner==b.owner&&a.peer==b.peer&&
         a.keyTag==b.keyTag&&a.role==b.role;
}
inline Recovered inspect(bool haveA,const uint8_t* a,
                         bool haveB,const uint8_t* b,
                         const Binding& expected){
  Recovered result={};
  result.status=Status::Absent;
  if(!haveA&&!haveB)return result;
  result.status=Status::Degraded; // fail closed on a missing/corrupt slot
  if(!haveA||!haveB)return result;
  Record x={},y={};
  if(!decode(a,IMAGE_BYTES,x)||!decode(b,IMAGE_BYTES,y))return result;
  if(!bindingMatches(x.bind,expected)||
     !bindingMatches(y.bind,expected)){
    result.status=Status::Mismatch;return result;
  }
  if(x.generation==y.generation){
    if(memcmp(a,b,IMAGE_BYTES)!=0)return result;
    result.newestSlot=1;result.snapshot=y;
  }else if(x.generation>y.generation){
    if(x.generation-y.generation!=1)return result;
    result.newestSlot=0;result.snapshot=x;
  }else{
    if(y.generation-x.generation!=1)return result;
    result.newestSlot=1;result.snapshot=y;
  }
  result.status=Status::Healthy;
  return result;
}
inline bool next(const Recovered& current,const Record& target,
                 Record& revised,uint8_t& writeSlot){
  if(current.status!=Status::Healthy ||
     current.snapshot.generation==UINT64_MAX ||
     !bindingMatches(current.snapshot.bind,target.bind))return false;
  revised=target;
  revised.generation=current.snapshot.generation+1;
  if(!valid(revised))return false;
  writeSlot=(uint8_t)(current.newestSlot^1U);
  return true;
}
} // namespace blaze_journal
