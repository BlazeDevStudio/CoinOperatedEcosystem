#pragma once
// Stage 5 remote-CS flash journal. Never autoformat or silently delete money.
#include "RemoteCsCodec.h"
static const char* REMOTE_SLOT0="/remote-cs0";
static const char* REMOTE_SLOT1="/remote-cs1";
static const char* REMOTE_TEMP="/remote-cstmp";
blaze_remote::Record remoteRecord={};
bool remoteJournalHealthy=false;
bool remoteJournalPresent=false;
bool remoteJournalWriteFailed=false;
bool remoteJournalFsReady=false;

bool remoteCsBinding(blaze_remote::Record& r) {
 if(interconPref.role!=INTERCON_REMOTE || !interconFileSystemReady ||
    !peerPairReady||!interconConfigHealthy)return false;
 r={};
 r.owner=ESP.getChipId();r.controller=peerPair.peerChip;
 if(!r.owner||!r.controller||r.owner==r.controller)return false;
 static const char label[]="BLAZE-REMOTE-CS-KEY-v1";
 uint8_t digest[32]={};
 if(!blaze_peer::hmacSha256(peerPair.key,label,sizeof(label)-1,digest))return false;
 memcpy(r.keyTag,digest,16);
 return true;
}
bool remoteRead(const char* file,uint8_t image[blaze_remote::JOURNAL_BYTES]) {
 File f=LittleFS.open(file,"r");if(!f)return false;
 const bool good=f.size()==blaze_remote::JOURNAL_BYTES &&
   f.read(image,blaze_remote::JOURNAL_BYTES)==(int)blaze_remote::JOURNAL_BYTES;
 f.close();return good;
}
void remoteRecover(bool fsReady){
 remoteJournalFsReady=fsReady;
 remoteJournalHealthy=false;
 remoteJournalPresent=fsReady&&(LittleFS.exists(REMOTE_SLOT0)||LittleFS.exists(REMOTE_SLOT1));
 remoteRecord={};
 if(!fsReady||!remoteJournalPresent)return;
 blaze_remote::Record binding={};
 if(!remoteCsBinding(binding))return;
 if(!LittleFS.exists(REMOTE_SLOT0)||!LittleFS.exists(REMOTE_SLOT1))return;
 uint8_t a[blaze_remote::JOURNAL_BYTES]={},b[blaze_remote::JOURNAL_BYTES]={};
 if(!remoteRead(REMOTE_SLOT0,a)||!remoteRead(REMOTE_SLOT1,b))return;
 blaze_remote::Record ra={},rb={};
 if(!blaze_remote::decodeRecord(a,sizeof(a),binding,ra) ||
    !blaze_remote::decodeRecord(b,sizeof(b),binding,rb))return;
 // One slot may be the older committed generation. Both must be readable.
 if(ra.generation>rb.generation+1 || rb.generation>ra.generation+1)return;
 remoteRecord=ra.generation>=rb.generation?ra:rb;
 remoteJournalHealthy=!remoteJournalWriteFailed;
}
bool remoteWriteSlot(const char* dest,const blaze_remote::Record& record){
 uint8_t img[blaze_remote::JOURNAL_BYTES]={};
 if(!remoteJournalFsReady || !blaze_remote::encodeRecord(record,img))return false;
 if(LittleFS.exists(REMOTE_TEMP)&&!LittleFS.remove(REMOTE_TEMP))return false;
 File f=LittleFS.open(REMOTE_TEMP,"w");if(!f)return false;
 const size_t n=f.write(img,sizeof(img));f.flush();f.close();
 uint8_t verify[blaze_remote::JOURNAL_BYTES]={};
 if(n!=sizeof(img)||!remoteRead(REMOTE_TEMP,verify)||memcmp(img,verify,sizeof(img)))
   return false;
 if(!LittleFS.rename(REMOTE_TEMP,dest)||!remoteRead(dest,verify)||
    memcmp(img,verify,sizeof(img)))return false;
 return true;
}
bool remoteInitialize(){
 if(interconPref.role!=INTERCON_REMOTE||!remoteJournalFsReady||
    remoteJournalPresent||remoteJournalWriteFailed||
    LittleFS.exists(REMOTE_SLOT0)||LittleFS.exists(REMOTE_SLOT1))return false;
 blaze_remote::Record r={};
 if(!remoteCsBinding(r))return false;
 r.generation=1;
 if(!remoteWriteSlot(REMOTE_SLOT0,r)||!remoteWriteSlot(REMOTE_SLOT1,r)){
  remoteJournalWriteFailed=true;return false;
 }
 remoteRecover(true);
 return remoteJournalHealthy;
}
bool remoteCommit(const blaze_remote::Record& candidate){
 if(!remoteJournalHealthy||remoteJournalWriteFailed||
    remoteRecord.generation==UINT64_MAX)return false;
 blaze_remote::Record next=candidate;
 next.generation=remoteRecord.generation+1;
 if(next.owner!=remoteRecord.owner||next.controller!=remoteRecord.controller||
    memcmp(next.keyTag,remoteRecord.keyTag,16))return false;
 const char* dest=(next.generation%2==0)?REMOTE_SLOT0:REMOTE_SLOT1;
 if(!remoteWriteSlot(dest,next)){
  remoteJournalWriteFailed=true;remoteJournalHealthy=false;return false;
 }
 remoteRecover(true);
 if(!remoteJournalHealthy||remoteRecord.generation!=next.generation){
  remoteJournalWriteFailed=true;remoteJournalHealthy=false;return false;
 }
 return true;
}
const char* remoteJournalStatus(){
 if(interconPref.role!=INTERCON_REMOTE)return "not-remote";
 if(!remoteJournalFsReady)return "filesystem-error";
 if(remoteJournalWriteFailed)return "write-failed";
 if(!remoteJournalPresent)return "uninitialized";
 return remoteJournalHealthy?"healthy":"degraded-or-binding-mismatch";
}
