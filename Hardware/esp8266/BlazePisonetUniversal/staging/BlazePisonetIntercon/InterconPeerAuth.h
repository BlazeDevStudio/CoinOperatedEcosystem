#pragma once
// BLAZE INTERCON v2: signed pairing and single paired-peer message dispatch.
// Actual paid events are only handled by the Stage 4 transaction layer, which
// must durably commit the journal before changing time or sending ACK.
// Discovery alone never authorizes payment, relays or CS.
#include "InterconSecureWire.h"
#include <stddef.h>
void interconHandleCredit(const blaze_peer::Frame& frame);
void interconHandleAck(const blaze_peer::Frame& frame);

static const uint32_t INTERCON_PAIR_MAGIC=0x42504132UL;
struct InterconPairConfig {
  uint32_t magic;
  uint32_t peerChip;
  char peerIp[16];
  uint8_t key[32];
  uint32_t checksum;
};
InterconPairConfig peerPair={};
bool peerPairReady=false;
uint32_t peerLastProof=0,peerLastHello=0;
uint32_t peerChallengeHigh=0,peerChallengeLow=0;
uint32_t peerFailedAuth=0;
bool peerChallengeOutstanding=false;

uint32_t peerConfigChecksum(const InterconPairConfig& cfg){
  const uint8_t* b=reinterpret_cast<const uint8_t*>(&cfg);
  uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(InterconPairConfig,checksum);i++)h=(h^b[i])*16777619UL;
  return h;
}
void peerLoadConfig(bool fsReady){
  peerPairReady=false;
  memset(&peerPair,0,sizeof(peerPair));
  if(!fsReady)return;
  File f=LittleFS.open("/blaze-peer-auth.cfg","r");
  if(!f)return;
  InterconPairConfig cfg={};
  const bool complete=(f.size()==sizeof(cfg)&&
                        f.readBytes(reinterpret_cast<char*>(&cfg),sizeof(cfg))==sizeof(cfg));
  f.close();
  IPAddress addr;
  if(!complete||cfg.magic!=INTERCON_PAIR_MAGIC||
     cfg.checksum!=peerConfigChecksum(cfg)||!cfg.peerChip||
     !memchr(cfg.peerIp,0,sizeof(cfg.peerIp))||
     !addr.fromString(cfg.peerIp)||addr==(uint32_t)0 ||
     cfg.peerChip==ESP.getChipId()) {
    Serial.println(F("[INTERCON] Peer credentials invalid; link disabled"));
    return;
  }
  peerPair=cfg;peerPairReady=true;
}
bool peerSaveConfig(const InterconPairConfig& request) {
  if(!interconFileSystemReady||!request.peerChip)return false;
  InterconPairConfig cfg=request;
  cfg.magic=INTERCON_PAIR_MAGIC;
  cfg.checksum=peerConfigChecksum(cfg);
  File f=LittleFS.open("/blaze-peer-auth.tmp","w");
  if(!f)return false;
  const size_t n=f.write(reinterpret_cast<const uint8_t*>(&cfg),sizeof(cfg));
  f.flush();f.close();
  if(n!=sizeof(cfg)) {
    LittleFS.remove("/blaze-peer-auth.tmp");return false;
  }
  if(!LittleFS.rename("/blaze-peer-auth.tmp","/blaze-peer-auth.cfg"))return false;
  peerPair=cfg;peerPairReady=true;
  peerLastProof=0;peerChallengeOutstanding=false;
  return true;
}
int peerHexDigit(char c){
  if(c>='0'&&c<='9')return c-'0';
  if(c>='A'&&c<='F')return c-'A'+10;
  if(c>='a'&&c<='f')return c-'a'+10;
  return -1;
}
bool peerDecodeKey(const String& hex,uint8_t out[32]){
  if(hex.length()!=64)return false;
  uint8_t acc=0;
  for(size_t i=0;i<32;i++){
    const int a=peerHexDigit(hex[2*i]),b=peerHexDigit(hex[2*i+1]);
    if(a<0||b<0)return false;
    out[i]=(uint8_t)((a<<4)|b);acc|=out[i];
  }
  return acc!=0; // reject only the all-zero key; fresh random keys recommended
}
bool peerDecodeChip(const String& text,uint32_t& id){
  if(text.length()!=8)return false;
  uint32_t x=0;
  for(size_t i=0;i<8;i++){
    int n=peerHexDigit(text[i]);if(n<0)return false;
    x=(x<<4)|(uint32_t)n;
  }
  if(!x||x==ESP.getChipId())return false;
  id=x;return true;
}
bool peerOnline(){
  return peerPairReady && peerLastProof &&
         (uint32_t)(millis()-peerLastProof)<25000UL;
}
void peerSend(const blaze_peer::Frame& frame,const IPAddress& dest){
  if(!peerPairReady)return;
  char out[blaze_peer::MAX_WIRE]={};
  const size_t n=blaze_peer::encode(frame,peerPair.key,out);
  if(!n)return;
  interconUdp.beginPacket(dest,INTERCON_DISCOVERY_PORT);
  interconUdp.write(reinterpret_cast<const uint8_t*>(out),n);
  interconUdp.endPacket();
}
void interconSecureReceived(const char* data,int len,IPAddress sourceIP) {
  if(!peerPairReady||(interconPref.role!=INTERCON_MASTER && interconPref.role!=INTERCON_SLAVE)||!interconPref.staEnabled||
     WiFi.status()!=WL_CONNECTED||len<=0||len>=(int)blaze_peer::MAX_WIRE)return;
  IPAddress approved;
  if(!approved.fromString(peerPair.peerIp)||sourceIP!=approved)return;
  blaze_peer::Frame input={};
  if(!blaze_peer::decode(data,(size_t)len,peerPair.key,
                         peerPair.peerChip,ESP.getChipId(),input)){
    if(peerFailedAuth<UINT32_MAX)peerFailedAuth++;
    return;
  }
  if(!strcmp(input.kind,"PING")){
    blaze_peer::Frame reply={};
    memcpy(reply.kind,"PONG",5);
    reply.source=ESP.getChipId();reply.destination=peerPair.peerChip;
    reply.eventHigh=input.eventHigh;reply.eventLow=input.eventLow;
    reply.units=0;
    peerSend(reply,approved);
    // Incoming signed PING proves possession of the shared key. We still
    // require our own fresh challenge response before marking peer online.
  } else if(!strcmp(input.kind,"PONG")){
    if(peerChallengeOutstanding && input.eventHigh==peerChallengeHigh &&
       input.eventLow==peerChallengeLow){
      peerLastProof=millis();peerChallengeOutstanding=false;
    }
  } else if(!strcmp(input.kind,"CRED")) {
    // Signed and correctly addressed, but only the owner role's durable
    // journal and paired live handshake can authorize credit application.
    interconHandleCredit(input);
  } else if(!strcmp(input.kind,"ACKN")) {
    interconHandleAck(input);
  }
}
void interconSecureTick(){
  if(!peerPairReady||!interconPref.staEnabled||
     (interconPref.role!=INTERCON_MASTER && interconPref.role!=INTERCON_SLAVE)||WiFi.status()!=WL_CONNECTED)return;
  const uint32_t now=millis();
  if((uint32_t)(now-peerLastHello)<7000UL)return;
  peerLastHello=now;
  IPAddress dest;
  if(!dest.fromString(peerPair.peerIp))return;
  peerChallengeHigh=ESP.random();peerChallengeLow=ESP.random();
  peerChallengeOutstanding=true;
  blaze_peer::Frame ping={};
  memcpy(ping.kind,"PING",5);
  ping.source=ESP.getChipId();ping.destination=peerPair.peerChip;
  ping.eventHigh=peerChallengeHigh;ping.eventLow=peerChallengeLow;
  ping.units=0;
  peerSend(ping,dest);
}
