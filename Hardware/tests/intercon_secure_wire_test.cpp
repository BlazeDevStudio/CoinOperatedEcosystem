// Portable host tests for the exact ESP8266 INTERCON HMAC wire codec.
#include <cstdio>
#include <cstring>
#include <cassert>
#include <string>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconSecureWire.h"

int main(){
  uint8_t key[32];for(int i=0;i<32;i++)key[i]=(uint8_t)i;
  blaze_peer::Frame a={};
  memcpy(a.kind,"PING",5);
  a.source=0xAABBCCDD;a.destination=0x11223344;
  a.eventHigh=0x01234567;a.eventLow=0x89ABCDEF;a.units=0;
  char msg[blaze_peer::MAX_WIRE]={};
  size_t n=blaze_peer::encode(a,key,msg);
  assert(n>100&&n<blaze_peer::MAX_WIRE);
  assert(std::string(msg)=="BLZ2|PING|AABBCCDD|11223344|01234567|89ABCDEF|0|C05C7E4E2A7597346B8F75BEFBE05B0BA22351E5CC84247FDC72163507F915BD");
  blaze_peer::Frame decoded={};
  assert(blaze_peer::decode(msg,n,key,a.source,a.destination,decoded));
  assert(decoded.eventHigh==a.eventHigh&&decoded.eventLow==a.eventLow&&decoded.units==0);
  assert(!blaze_peer::decode(msg,n,key,a.destination,a.source,decoded));
  assert(!blaze_peer::decode(msg,n-1,key,a.source,a.destination,decoded));
  uint8_t wrongKey[32]={};
  assert(!blaze_peer::decode(msg,n,wrongKey,a.source,a.destination,decoded));
  char bad[blaze_peer::MAX_WIRE]={};
  memcpy(bad,msg,n+1);bad[10]^=1;
  assert(!blaze_peer::decode(bad,n,key,a.source,a.destination,decoded));
  memcpy(bad,msg,n+1);bad[n-1]^=1;
  assert(!blaze_peer::decode(bad,n,key,a.source,a.destination,decoded));
  memcpy(bad,msg,n+1);bad[15]=0;
  assert(!blaze_peer::decode(bad,n,key,a.source,a.destination,decoded));
  // Valid remote credit envelope format MUST NOT imply permission to apply it:
  // the runtime handler recognizes ONLY signed PING/PONG.
  memcpy(a.kind,"CRED",5);a.units=90;
  n=blaze_peer::encode(a,key,msg);
  assert(blaze_peer::decode(msg,n,key,a.source,a.destination,decoded));
  assert(decoded.units==90);
  memcpy(a.kind,"PONG",5);a.units=1;
  assert(blaze_peer::encode(a,key,msg)==0);
  puts("PASS: real HMAC-SHA256 KAT, signed PING, tampering, wrong identity/key, bounded parse");
  return 0;
}
