#pragma once
// BLAZE INTERCON v2: fixed-format authenticated peer envelopes.
// Security property: message authenticity only. PING/PONG are permitted;
// CRED/ACK types are reserved but MUST NOT modify balances until a separate
// durable target-bound coin journal is validated. This header has no GUI/IO.
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#ifdef ARDUINO
#include <bearssl/bearssl.h>
#else
#include <openssl/hmac.h>
#endif

namespace blaze_peer {
static const size_t KEY_BYTES=32;
static const size_t TAG_HEX=64;
static const size_t MAX_WIRE=152;
struct Frame {
  char kind[5];          // PING/PONG/CRED/ACKN
  uint32_t source;       // unique ESP chip ID (not sufficient for trust)
  uint32_t destination;
  uint32_t eventHigh;
  uint32_t eventLow;
  uint16_t units;        // 0 for PING/PONG/ACKN; ignored for remote credit
};
inline char hexDigit(uint8_t x) {return "0123456789ABCDEF"[x&15];}
inline bool isHexUpper(char c) {return (c>='0'&&c<='9')||(c>='A'&&c<='F');}
inline bool parseHex32(const char* p,size_t n,uint32_t& out) {
  if(n!=8)return false;
  uint32_t v=0;
  for(size_t i=0;i<8;i++){
    if(!isHexUpper(p[i]))return false;
    v=(v<<4)|((p[i]<='9')?(p[i]-'0'):(p[i]-'A'+10));
  }
  out=v;return true;
}
inline bool parseUnits(const char* p,size_t n,uint16_t& out) {
  if(!n||n>5||(n>1&&p[0]=='0'))return false;
  uint32_t u=0;
  for(size_t i=0;i<n;i++){if(p[i]<'0'||p[i]>'9')return false;u=u*10+(uint8_t)(p[i]-'0');}
  if(u>65535)return false;
  out=(uint16_t)u;return true;
}
inline bool typeAllowed(const char* p,size_t n) {
  if(n!=4)return false;
  return !memcmp(p,"PING",4)||!memcmp(p,"PONG",4)||
         !memcmp(p,"CRED",4)||!memcmp(p,"ACKN",4);
}
inline bool hmacSha256(const uint8_t key[KEY_BYTES],
                       const void* data,size_t length,uint8_t out[32]){
#ifdef ARDUINO
  br_hmac_key_context kc;
  br_hmac_context hc;
  br_hmac_key_init(&kc,&br_sha256_vtable,key,KEY_BYTES);
  br_hmac_init(&hc,&kc,32);
  br_hmac_update(&hc,data,length);
  br_hmac_out(&hc,out);
  return true;
#else
  unsigned int n=0;
  return HMAC(EVP_sha256(),key,KEY_BYTES,
              static_cast<const unsigned char*>(data),length,out,&n)!=nullptr&&n==32;
#endif
}
inline bool macHex(const uint8_t key[KEY_BYTES],const char* bytes,size_t n,
                   char out[TAG_HEX+1]) {
  uint8_t digest[32];
  if(!hmacSha256(key,bytes,n,digest))return false;
  for(size_t i=0;i<32;i++){
    out[2*i]=hexDigit(digest[i]>>4);
    out[2*i+1]=hexDigit(digest[i]);
  }
  out[TAG_HEX]=0;
  return true;
}
inline bool equalTag(const char* supplied,const char* expected) {
  uint8_t difference=0;
  for(size_t i=0;i<TAG_HEX;i++) difference|=(uint8_t)(supplied[i]^expected[i]);
  return difference==0; // constant work independent of first differing byte
}
inline size_t encode(const Frame& frame,const uint8_t key[KEY_BYTES],
                     char wire[MAX_WIRE]) {
  if(!typeAllowed(frame.kind,4)||frame.kind[4]!=0||
     !frame.source||!frame.destination||
     ((memcmp(frame.kind,"PING",4)==0||memcmp(frame.kind,"PONG",4)==0||
       memcmp(frame.kind,"ACKN",4)==0) && frame.units!=0))return 0;
  const int n=snprintf(wire,MAX_WIRE,"BLZ2|%.4s|%08lX|%08lX|%08lX|%08lX|%u|",
                      frame.kind,(unsigned long)frame.source,
                      (unsigned long)frame.destination,
                      (unsigned long)frame.eventHigh,
                      (unsigned long)frame.eventLow,(unsigned int)frame.units);
  if(n<=0||(size_t)n+TAG_HEX+1>MAX_WIRE)return 0;
  char tag[TAG_HEX+1];
  if(!macHex(key,wire,(size_t)n,tag))return 0;
  memcpy(wire+n,tag,TAG_HEX+1);
  return (size_t)n+TAG_HEX;
}
inline bool decode(const char* wire,size_t n,const uint8_t key[KEY_BYTES],
                   uint32_t expectedPeer,uint32_t localChip,Frame& out) {
  if(!wire||n<109||n>=MAX_WIRE||!expectedPeer||!localChip)return false;
  // Exact seven pipe delimiters; fixed uppercase hex, no escaping or NUL.
  const char* fields[8]={};size_t length[8]={};
  size_t index=0,start=0;
  for(size_t i=0;i<n;i++){
    if(!wire[i])return false;
    if(wire[i]=='|'){
      if(index>=7)return false;
      fields[index]=wire+start;
      length[index]=i-start;
      index++;start=i+1;
    }
  }
  if(index!=7)return false;
  fields[7]=wire+start;length[7]=n-start;
  if(length[0]!=4||memcmp(fields[0],"BLZ2",4)!=0||
     !typeAllowed(fields[1],length[1])||
     length[7]!=TAG_HEX)return false;
  Frame parsed={};
  memcpy(parsed.kind,fields[1],4);
  if(!parseHex32(fields[2],length[2],parsed.source)||
     !parseHex32(fields[3],length[3],parsed.destination)||
     !parseHex32(fields[4],length[4],parsed.eventHigh)||
     !parseHex32(fields[5],length[5],parsed.eventLow)||
     !parseUnits(fields[6],length[6],parsed.units))return false;
  if(parsed.source!=expectedPeer||parsed.destination!=localChip)return false;
  if((memcmp(parsed.kind,"PING",4)==0||memcmp(parsed.kind,"PONG",4)==0||
      memcmp(parsed.kind,"ACKN",4)==0)&&parsed.units!=0)return false;
  for(size_t i=0;i<TAG_HEX;i++)if(!isHexUpper(fields[7][i]))return false;
  char correct[TAG_HEX+1];
  if(!macHex(key,wire,(size_t)(fields[7]-wire),correct))return false;
  if(!equalTag(fields[7],correct))return false;
  out=parsed;return true;
}
} // namespace blaze_peer
