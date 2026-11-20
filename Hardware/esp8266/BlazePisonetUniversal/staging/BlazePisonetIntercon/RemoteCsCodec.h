#pragma once
// BLAZE Remote CS v1. Portable, explicit, authenticated router/controller wire.
// Original protocol; JuanFi is an architectural reference, not a wire peer.
#include "InterconSecureWire.h"
#include "InterconJournalCodec.h"
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

namespace blaze_remote {
static const size_t WIRE_MAX=192;
static const size_t JOURNAL_BYTES=84;
static const uint32_t JOURNAL_MAGIC=0x31435342UL; // BSC1
struct Message {
 char kind[5]; // OPEN, CLOS, ACKN, POLL; responses EVNT, EMPT, OKAY
 uint32_t source, destination;
 uint64_t command, session, event;
 uint16_t value;
};
struct Record {
 uint32_t owner=0,controller=0;
 uint8_t keyTag[16]={};
 uint64_t generation=0,lastCommand=0,eventCounter=0;
 uint64_t pendingEvent=0,pendingSession=0;
 uint32_t pendingPulses=0;
};
inline uint64_t read64(const uint8_t* p) {
 uint64_t v=0;for(int i=7;i>=0;--i)v=(v<<8)|p[i];return v;
}
inline void write64(uint8_t* p,uint64_t v) {
 for(int i=0;i<8;++i){p[i]=(uint8_t)v;v>>=8;}
}
inline bool kindAllowed(const char* s){
 return !memcmp(s,"OPEN",4)||!memcmp(s,"CLOS",4)||
        !memcmp(s,"ACKN",4)||!memcmp(s,"POLL",4)||
        !memcmp(s,"EVNT",4)||!memcmp(s,"EMPT",4)||
        !memcmp(s,"OKAY",4);
}
inline bool parse64(const char* p,size_t n,uint64_t& value){
 if(n!=16)return false;
 uint64_t x=0;
 for(size_t i=0;i<n;++i) {
  if(!blaze_peer::isHexUpper(p[i]))return false;
  x=(x<<4)|(p[i]<='9'?p[i]-'0':p[i]-'A'+10);
 }
 value=x;return true;
}
inline void hex64(uint64_t value,char out[17]){
 for(int i=15;i>=0;--i){out[i]=blaze_peer::hexDigit(value);value>>=4;}
 out[16]=0;
}
inline size_t encode(const Message& m,const uint8_t key[32],char out[WIRE_MAX]){
 if(!kindAllowed(m.kind)||m.kind[4]!=0||!m.source||!m.destination)return 0;
 char cs[17],se[17],ev[17];hex64(m.command,cs);hex64(m.session,se);hex64(m.event,ev);
 const int n=snprintf(out,WIRE_MAX,"BLZCS1|%.4s|%08lX|%08lX|%s|%s|%s|%u|",
                    m.kind,(unsigned long)m.source,(unsigned long)m.destination,
                    cs,se,ev,(unsigned)m.value);
 if(n<=0||(size_t)n+blaze_peer::TAG_HEX+1>WIRE_MAX)return 0;
 char tag[65];if(!blaze_peer::macHex(key,out,(size_t)n,tag))return 0;
 memcpy(out+n,tag,65);return (size_t)n+64;
}
inline bool decode(const char* data,size_t n,const uint8_t key[32],
                   uint32_t expectedSource,uint32_t expectedDestination,Message& out){
 if(!data||n<130||n>=WIRE_MAX)return false;
 const char* fields[9]={};size_t lengths[9]={};size_t idx=0,start=0;
 for(size_t i=0;i<n;i++){
  if(!data[i])return false;
  if(data[i]=='|'){
   if(idx>=8)return false;
   fields[idx]=data+start;lengths[idx]=i-start;
   ++idx;start=i+1;
  }
 }
 if(idx!=8)return false;
 fields[8]=data+start;lengths[8]=n-start;
 if(lengths[0]!=6||memcmp(fields[0],"BLZCS1",6)||
    lengths[1]!=4||lengths[8]!=64)return false;
 Message parsed={};memcpy(parsed.kind,fields[1],4);
 if(!kindAllowed(parsed.kind)||!blaze_peer::parseHex32(fields[2],lengths[2],parsed.source)||
    !blaze_peer::parseHex32(fields[3],lengths[3],parsed.destination)||
    !parse64(fields[4],lengths[4],parsed.command)||
    !parse64(fields[5],lengths[5],parsed.session)||
    !parse64(fields[6],lengths[6],parsed.event)||
    !blaze_peer::parseUnits(fields[7],lengths[7],parsed.value)||
    parsed.source!=expectedSource||parsed.destination!=expectedDestination)
   return false;
 for(size_t i=0;i<64;++i)if(!blaze_peer::isHexUpper(fields[8][i]))return false;
 char tag[65];if(!blaze_peer::macHex(key,data,(size_t)(fields[8]-data),tag)||
                  !blaze_peer::equalTag(fields[8],tag))return false;
 out=parsed;return true;
}
inline bool encodeRecord(const Record& r,uint8_t out[JOURNAL_BYTES]){
 if(!r.owner||!r.controller||r.owner==r.controller||!r.generation||
    (r.pendingPulses>20)||((r.pendingEvent==0)!=(r.pendingPulses==0))||
    ((r.pendingEvent==0)!=(r.pendingSession==0)))return false;
 uint8_t nz=0;for(uint8_t b:r.keyTag)nz|=b;if(!nz)return false;
 memset(out,0,JOURNAL_BYTES);
 blaze_journal::w32(out,JOURNAL_MAGIC);
 blaze_journal::w32(out+4,1);
 blaze_journal::w32(out+8,r.owner);
 blaze_journal::w32(out+12,r.controller);
 memcpy(out+16,r.keyTag,16);
 write64(out+32,r.generation);
 write64(out+40,r.lastCommand);
 write64(out+48,r.eventCounter);
 write64(out+56,r.pendingEvent);
 write64(out+64,r.pendingSession);
 blaze_journal::w32(out+72,r.pendingPulses);
 blaze_journal::w32(out+80,blaze_journal::crc32(out,80));
 return true;
}
inline bool decodeRecord(const uint8_t* p,size_t n,const Record& binding,Record& r){
 if(!p||n!=JOURNAL_BYTES||blaze_journal::r32(p)!=JOURNAL_MAGIC||
    blaze_journal::r32(p+4)!=1||
    blaze_journal::r32(p+80)!=blaze_journal::crc32(p,80)||
    blaze_journal::r32(p+8)!=binding.owner||
    blaze_journal::r32(p+12)!=binding.controller||
    memcmp(p+16,binding.keyTag,16))return false;
 Record candidate=binding;
 candidate.generation=read64(p+32);
 candidate.lastCommand=read64(p+40);
 candidate.eventCounter=read64(p+48);
 candidate.pendingEvent=read64(p+56);
 candidate.pendingSession=read64(p+64);
 candidate.pendingPulses=blaze_journal::r32(p+72);
 if(!candidate.generation||candidate.pendingPulses>20||
    ((candidate.pendingEvent==0)!=(candidate.pendingPulses==0))||
    ((candidate.pendingEvent==0)!=(candidate.pendingSession==0))||
    candidate.pendingEvent>candidate.eventCounter)return false;
 r=candidate;return true;
}
} // blaze_remote
