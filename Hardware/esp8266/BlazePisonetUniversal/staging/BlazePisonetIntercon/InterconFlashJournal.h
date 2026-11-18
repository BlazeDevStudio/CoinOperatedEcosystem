#pragma once
// LittleFS adapter for the canonical BLAZE INTERCON Stage 3 journal.
// Included AFTER InterconPeerAuth.h. No remote credit, relay, CS, or timer
// operations are executed here. Only an AP-authorized idle lab initialization
// can create a pristine journal; read-only boot recovery otherwise.
#include "InterconJournalCodec.h"

static const char* JOURNAL_SLOT0="/intercon-j0";
static const char* JOURNAL_SLOT1="/intercon-j1";
static const char* JOURNAL_TEMP="/intercon-jtmp";
blaze_journal::Recovered interconRecovered={};
bool interconJournalFsReady=false;
bool interconJournalPairReady=false;
bool interconJournalWriteFailed=false;

bool interconJournalBinding(blaze_journal::Binding& out) {
  if(!interconFileSystemReady || !peerPairReady ||
     !interconConfigHealthy ||
     (interconPref.role!=INTERCON_MASTER && interconPref.role!=INTERCON_SLAVE))
    return false;
  // Truncated HMAC is used as a key-change *binding*, not network auth.
  // The full 256-bit HMAC is verified on each authenticated network packet.
  static const char label[]="BLZJ-PAIR-BIND-v1";
  uint8_t digest[32]={};
  if(!blaze_peer::hmacSha256(peerPair.key,label,sizeof(label)-1,digest))
    return false;
  out.owner=ESP.getChipId();
  out.peer=peerPair.peerChip;
  out.keyTag=((uint32_t)digest[0]<<24) | ((uint32_t)digest[1]<<16) |
             ((uint32_t)digest[2]<<8) | digest[3];
  out.role=interconPref.role;
  return out.owner && out.peer && out.keyTag && out.owner!=out.peer;
}
const char* interconJournalStatusName(){
  if(!interconJournalFsReady)return "unavailable";
  if(interconPref.role==INTERCON_STANDARD)return "standard";
  if(!interconJournalPairReady)return "unpaired";
  if(interconJournalWriteFailed)return "write-failed";
  switch(interconRecovered.status){
    case blaze_journal::Status::Absent:return "uninitialized";
    case blaze_journal::Status::Healthy:return "healthy";
    case blaze_journal::Status::Degraded:return "degraded";
    case blaze_journal::Status::Mismatch:return "binding-mismatch";
  }
  return "unknown";
}
bool interconJournalReadSlot(const char* path,uint8_t out[blaze_journal::IMAGE_BYTES]){
  memset(out,0,blaze_journal::IMAGE_BYTES);
  File f=LittleFS.open(path,"r");
  if(!f)return false;
  bool complete=f.size()==blaze_journal::IMAGE_BYTES &&
                 f.read(out,blaze_journal::IMAGE_BYTES)==
                 (int)blaze_journal::IMAGE_BYTES;
  f.close();
  return complete;
}
void interconJournalRecover(bool fsReady) {
  interconJournalFsReady=fsReady;
  interconJournalWriteFailed=false;
  interconJournalPairReady=false;
  interconRecovered={};
  interconRecovered.status=blaze_journal::Status::Absent;
  if(!fsReady)return;
  blaze_journal::Binding expected={};
  if(!interconJournalBinding(expected))return;
  interconJournalPairReady=true;
  uint8_t a[blaze_journal::IMAGE_BYTES]={};
  uint8_t b[blaze_journal::IMAGE_BYTES]={};
  const bool haveA=LittleFS.exists(JOURNAL_SLOT0);
  const bool haveB=LittleFS.exists(JOURNAL_SLOT1);
  // An existing but incomplete/unreadable slot is CORRUPT, not absent.
  const bool okA=!haveA||interconJournalReadSlot(JOURNAL_SLOT0,a);
  const bool okB=!haveB||interconJournalReadSlot(JOURNAL_SLOT1,b);
  if(!okA||!okB){
    interconRecovered.status=blaze_journal::Status::Degraded;
    return;
  }
  interconRecovered=blaze_journal::inspect(haveA,a,haveB,b,expected);
}
bool interconJournalAtomicReplace(const char* destination,
                                  const uint8_t bytes[blaze_journal::IMAGE_BYTES]){
  if(!interconJournalFsReady)return false;
  if(LittleFS.exists(JOURNAL_TEMP)&&!LittleFS.remove(JOURNAL_TEMP))
    return false; // old interrupted temp is safe to discard, never a slot
  File f=LittleFS.open(JOURNAL_TEMP,"w");
  if(!f)return false;
  const size_t written=f.write(bytes,blaze_journal::IMAGE_BYTES);
  f.flush();
  f.close();
  uint8_t check[blaze_journal::IMAGE_BYTES]={};
  if(written!=blaze_journal::IMAGE_BYTES ||
     !interconJournalReadSlot(JOURNAL_TEMP,check) ||
     memcmp(check,bytes,blaze_journal::IMAGE_BYTES)!=0)
    return false;
  // LittleFS metadata rename is atomic on a healthy filesystem. The other
  // complete slot is NOT removed or rewritten during this operation.
  if(!LittleFS.rename(JOURNAL_TEMP,destination))return false;
  memset(check,0,sizeof(check));
  return interconJournalReadSlot(destination,check) &&
         memcmp(check,bytes,blaze_journal::IMAGE_BYTES)==0;
}
bool interconJournalInitialize() {
  if(!interconJournalFsReady || !interconJournalPairReady ||
     interconJournalWriteFailed ||
     interconRecovered.status!=blaze_journal::Status::Absent)return false;
  // No implicit reset: any corrupt/existing slot must be reconciled by an
  // operator outside this firmware. Never drop an unknown paid history.
  if(LittleFS.exists(JOURNAL_SLOT0)||LittleFS.exists(JOURNAL_SLOT1))
    return false;
  blaze_journal::Binding binding={};
  if(!interconJournalBinding(binding))return false;
  blaze_journal::Record pristine={};
  pristine.bind=binding;
  pristine.generation=1;
  pristine.slave.authorizedIssuer=binding.peer;
  uint8_t image[blaze_journal::IMAGE_BYTES]={};
  if(!blaze_journal::encode(pristine,image))return false;
  // Two identical generation-1 slots permit the next update to be atomic.
  if(!interconJournalAtomicReplace(JOURNAL_SLOT0,image) ||
     !interconJournalAtomicReplace(JOURNAL_SLOT1,image)){
    interconJournalWriteFailed=true;
    return false;
  }
  interconJournalRecover(true);
  return interconRecovered.status==blaze_journal::Status::Healthy;
}
bool interconJournalCommit(const blaze_journal::Record& target){
  // API reserved for the future atomic timer/receipt integration. DO NOT
  // invoke from the current Master/Slave coin path (which stays locked).
  if(interconJournalWriteFailed ||
     interconRecovered.status!=blaze_journal::Status::Healthy)return false;
  blaze_journal::Record next={};
  uint8_t dest=0;
  if(!blaze_journal::next(interconRecovered,target,next,dest))return false;
  uint8_t image[blaze_journal::IMAGE_BYTES]={};
  if(!blaze_journal::encode(next,image))return false;
  if(!interconJournalAtomicReplace(dest?JOURNAL_SLOT1:JOURNAL_SLOT0,image)){
    interconJournalWriteFailed=true; // fail-stop: don't retry the same coin
    return false;
  }
  interconJournalRecover(true);
  if(interconRecovered.status!=blaze_journal::Status::Healthy ||
     interconRecovered.snapshot.generation!=next.generation){
    interconJournalWriteFailed=true;
    return false;
  }
  return true;
}
