#pragma once
// LittleFS adapter for portable BLAZE INTERCON dual-slot journal.
// The active slot is NEVER removed. Write tmp, flush, close, verify, then
// replace ONLY the inactive slot. No claim of power-loss atomicity on all
// ESP8266 flash chips without physical fault-injection validation.
#include <LittleFS.h>
#include "InterconDurableJournal.h"
struct InterconJournalFS {
  const char* prefix;
  bool mounted;
  explicit InterconJournalFS(const char*p,bool fs):prefix(p),mounted(fs){}
  String name(char slot)const{
    String result(prefix);
    result+=(slot=='A'?"-a":"-b");
    return result;
  }
  static bool readSlot(void*context,char slot,uint8_t out[blaze_journal::RECORD_SIZE],
                       size_t& actual){
    auto& io=*static_cast<InterconJournalFS*>(context);
    actual=0;
    if(!io.mounted||(slot!='A'&&slot!='B'))return false;
    const String path=io.name(slot);
    if(!LittleFS.exists(path))return true;
    File f=LittleFS.open(path,"r");
    if(!f)return false;
    actual=f.size();
    if(actual==0)actual=1; // Existing empty file is CORRUPT, not absent.
    if(actual!=blaze_journal::RECORD_SIZE){f.close();return true;}
    const size_t got=f.read(out,blaze_journal::RECORD_SIZE);
    f.close();
    return got==blaze_journal::RECORD_SIZE;
  }
  static bool writeSlot(void*context,char slot,
                        const uint8_t data[blaze_journal::RECORD_SIZE]){
    auto& io=*static_cast<InterconJournalFS*>(context);
    if(!io.mounted||(slot!='A'&&slot!='B'))return false;
    const String destination=io.name(slot);
    const String tmp=String(io.prefix)+".tmp";
    // Stale incomplete temp from prior power loss may be removed safely.
    if(LittleFS.exists(tmp)&&!LittleFS.remove(tmp))return false;
    File f=LittleFS.open(tmp,"w");
    if(!f)return false;
    const size_t wrote=f.write(data,blaze_journal::RECORD_SIZE);
    f.flush();f.close();
    if(wrote!=blaze_journal::RECORD_SIZE)return false;
    // Test entire temp before touching inactive destination.
    File check=LittleFS.open(tmp,"r");
    if(!check)return false;
    uint8_t bytes[blaze_journal::RECORD_SIZE]={};
    const size_t n=check.read(bytes,blaze_journal::RECORD_SIZE);
    const bool sized=check.size()==blaze_journal::RECORD_SIZE;
    check.close();
    if(n!=blaze_journal::RECORD_SIZE||!sized||
       memcmp(bytes,data,blaze_journal::RECORD_SIZE)!=0)return false;
    if(LittleFS.exists(destination)&&!LittleFS.remove(destination))return false;
    // Power loss here leaves the active valid slot untouched. Return false
    // on failure, leaving caller LOCKED (outcome possibly uncertain).
    return LittleFS.rename(tmp,destination);
  }
  blaze_journal::IO port(){
    return {&InterconJournalFS::readSlot,&InterconJournalFS::writeSlot,this};
  }
};
