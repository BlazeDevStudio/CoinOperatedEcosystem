#pragma once
// BLAZE INTERCON Stage 1 — local discovery only.
//
// SECURITY CONTRACT: no coin, time, power or configuration operations may be
// accepted from UDP discovery packets. Master/Slave money movement remains
// DISABLED until authenticated, durable, replay-safe peer credit is available.
// This file is part of a DRAFT laboratory build, not production firmware.

#include <WiFiUdp.h>
#include <stdlib.h>

enum InterconRole : uint8_t { INTERCON_STANDARD=0, INTERCON_MASTER=1, INTERCON_SLAVE=2 };
static const uint32_t INTERCON_CFG_MAGIC=0x42494E31UL;
static const uint16_t INTERCON_DISCOVERY_PORT=4210;
static const uint8_t INTERCON_MAX_PEERS=12;

struct InterconPreferences {
  uint32_t magic;
  uint8_t role;
  uint8_t staEnabled;
  char staSsid[33];
  char staPassword[65];
  uint32_t checksum;
};
struct InterconPeer {
  uint32_t chipId;
  IPAddress ip;
  uint32_t lastSeen;
};

InterconPreferences interconPref;
InterconPeer interconPeers[INTERCON_MAX_PEERS]={};
WiFiUDP interconUdp;
void interconSecureReceived(const char* data,int len,IPAddress remoteIp);
bool interconFileSystemReady=false;
bool interconConfigHealthy=true;
uint32_t interconLastAdvertised=0, interconLastReconnect=0;

void interconDefaults() {
  memset(&interconPref,0,sizeof(interconPref));
  interconPref.magic=INTERCON_CFG_MAGIC;
  interconPref.role=INTERCON_STANDARD;
}
uint32_t interconConfigChecksum() {
  const uint8_t* bytes=reinterpret_cast<const uint8_t*>(&interconPref);
  uint32_t hash=2166136261UL;
  for(size_t i=0;i<sizeof(interconPref)-sizeof(interconPref.checksum);++i)
    hash=(hash^bytes[i])*16777619UL;
  return hash;
}
void loadInterconConfig(bool fsReady) {
  interconFileSystemReady=fsReady;
  interconDefaults();
  interconConfigHealthy=fsReady;
  if(!fsReady) {
    // If storage is unavailable, do not assume Standard and accept coins.
    interconPref.role=INTERCON_SLAVE;
    Serial.println(F("[INTERCON] Storage unavailable; coin input locked"));
    return;
  }
  File f=LittleFS.open("/blaze-intercon.cfg","r");
  if(!f)return;
  InterconPreferences candidate={};
  size_t n=f.readBytes(reinterpret_cast<char*>(&candidate),sizeof(candidate));
  const bool complete=(n==sizeof(candidate) && !f.available());
  f.close();
  if(!complete) {
    interconConfigHealthy=false;
    interconPref.role=INTERCON_SLAVE;
    Serial.println(F("[INTERCON] Corrupt config length; coin input locked"));
    return;
  }
  interconPref=candidate;
  interconPref.staSsid[32]=0;
  interconPref.staPassword[64]=0;
  if(interconPref.magic!=INTERCON_CFG_MAGIC || interconPref.role>INTERCON_SLAVE ||
     interconPref.staEnabled>1 || interconPref.checksum!=interconConfigChecksum() ||
     strlen(interconPref.staSsid)>32 || strlen(interconPref.staPassword)>63) {
    interconDefaults();
    interconConfigHealthy=false;
    interconPref.role=INTERCON_SLAVE;
    Serial.println(F("[INTERCON] Invalid settings; coin input locked"));
  }
}
bool saveInterconConfig() {
  if(!interconFileSystemReady)return false;
  interconPref.magic=INTERCON_CFG_MAGIC;
  interconPref.checksum=interconConfigChecksum();
  File f=LittleFS.open("/blaze-intercon.tmp","w");
  if(!f)return false;
  const size_t written=f.write(reinterpret_cast<const uint8_t*>(&interconPref),sizeof(interconPref));
  f.flush();
  f.close();
  if(written!=sizeof(interconPref)) {
    LittleFS.remove("/blaze-intercon.tmp");
    return false;
  }
  // Do not delete the old settings if rename fails.
  if(!LittleFS.rename("/blaze-intercon.tmp","/blaze-intercon.cfg"))return false;
  interconConfigHealthy=true;
  return true;
}
bool interconLocalCoinsAllowed() {
  // Master/Slave hardware coin routing is intentionally locked while the
  // signed credit protocol is unfinished. Standard remains fully standalone.
  return interconConfigHealthy && csEnabled && interconPref.role==INTERCON_STANDARD;
}
uint8_t interconPeerCount() {
  const uint32_t now=millis();
  uint8_t count=0;
  for(uint8_t i=0;i<INTERCON_MAX_PEERS;i++)
    if(interconPeers[i].chipId && (uint32_t)(now-interconPeers[i].lastSeen)<30000UL)
      ++count;
  return count;
}
void interconReceiveDiscovery() {
  const int size=interconUdp.parsePacket();
  if(!size)return;
  if(size>32) {
    if(size>=(int)blaze_peer::MAX_WIRE) {
      while(interconUdp.available())interconUdp.read();
      return;
    }
    char frame[blaze_peer::MAX_WIRE]={};
    const int got=interconUdp.read(frame,size);
    if(got==size)interconSecureReceived(frame,got,interconUdp.remoteIP());
    return; // Financial, power and CS messages are NEVER accepted here.
  }
  char msg[33]={};
  const int len=interconUdp.read(msg,sizeof(msg)-1);
  if(len<8 || len>14 || strncmp(msg,"BLZD1:",6)!=0)return;
  for(int i=6;i<len;i++) {
    const char c=msg[i];
    if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')))return;
  }
  const uint32_t chip=(uint32_t)strtoul(msg+6,nullptr,16);
  if(!chip || chip==ESP.getChipId())return;
  int slot=-1;
  uint32_t oldestAge=0;
  const uint32_t now=millis();
  for(uint8_t i=0;i<INTERCON_MAX_PEERS;i++) {
    if(interconPeers[i].chipId==chip){slot=i;break;}
    if(!interconPeers[i].chipId){slot=i;break;}
    const uint32_t age=(uint32_t)(now-interconPeers[i].lastSeen);
    if(age>30000UL && age>oldestAge){oldestAge=age;slot=i;}
  }
  if(slot<0)return; // fixed-size bounded node table
  interconPeers[slot].chipId=chip;
  interconPeers[slot].ip=interconUdp.remoteIP();
  interconPeers[slot].lastSeen=now;
}
void interconAdvertise() {
  char msg[24];
  snprintf(msg,sizeof(msg),"BLZD1:%06lX",(unsigned long)ESP.getChipId());
  const IPAddress ap=WiFi.softAPIP();
  const IPAddress apBroadcast(ap[0],ap[1],ap[2],255);
  interconUdp.beginPacket(apBroadcast,INTERCON_DISCOVERY_PORT);
  interconUdp.write(reinterpret_cast<const uint8_t*>(msg),strlen(msg));
  interconUdp.endPacket();
  if(WiFi.status()==WL_CONNECTED) {
    const IPAddress a=WiFi.localIP(),m=WiFi.subnetMask();
    const IPAddress bcast((a[0]&m[0])|((uint8_t)~m[0]),
                          (a[1]&m[1])|((uint8_t)~m[1]),
                          (a[2]&m[2])|((uint8_t)~m[2]),
                          (a[3]&m[3])|((uint8_t)~m[3]));
    interconUdp.beginPacket(bcast,INTERCON_DISCOVERY_PORT);
    interconUdp.write(reinterpret_cast<const uint8_t*>(msg),strlen(msg));
    interconUdp.endPacket();
  }
}
void interconLoop() {
  interconReceiveDiscovery();
  const uint32_t now=millis();
  if((uint32_t)(now-interconLastAdvertised)>=10000UL) {
    interconLastAdvertised=now;
    interconAdvertise();
  }
  if(interconPref.staEnabled && interconPref.staSsid[0] &&
     WiFi.status()!=WL_CONNECTED &&
     (uint32_t)(now-interconLastReconnect)>=30000UL) {
    interconLastReconnect=now;
    WiFi.begin(interconPref.staSsid,interconPref.staPassword);
  }
}
