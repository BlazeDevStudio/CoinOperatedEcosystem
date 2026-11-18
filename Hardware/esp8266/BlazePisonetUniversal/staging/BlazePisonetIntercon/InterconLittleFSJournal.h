#pragma once
// ESP8266 LittleFS storage adapter for InterconDurableJournal.h.
// Separate files: /blaze-pay-A.bin and /blaze-pay-B.bin. Never erase/reformat
// LittleFS on journal errors, and never overwrite the currently active slot.
//
// This adapter deliberately exposes no automatic initialization. Pairing,
// reconciliation and paid-balance migration must be verified first.
#include <LittleFS.h>
#include "InterconDurableJournal.h"

class InterconLittleFSJournal : public blaze_durable::Storage {
  bool mounted_;
  const char* fileName(uint8_t slot) const {
    return slot==0 ? "/blaze-pay-A.bin" : "/blaze-pay-B.bin";
  }
public:
  explicit InterconLittleFSJournal(bool mounted):mounted_(mounted){}
  void setMounted(bool ready) {mounted_=ready;}
  blaze_durable::Read readSlot(uint8_t slot,uint8_t* bytes,size_t max,
                              size_t& count) override {
    count=0;
    if(slot>1||!mounted_||!bytes)return blaze_durable::Read::Error;
    const char* name=fileName(slot);
    if(!LittleFS.exists(name))return blaze_durable::Read::Missing;
    File f=LittleFS.open(name,"r");
    if(!f)return blaze_durable::Read::Error;
    const size_t actual=f.size();
    if(actual>max) {
      // Return Present with a nonconforming length; the strict codec will
      // classify it as corruption instead of allowing silent rollback.
      count=actual;
      f.close();
      return blaze_durable::Read::Present;
    }
    count=f.readBytes(reinterpret_cast<char*>(bytes),actual);
    const bool complete=(count==actual);
    f.close();
    return complete?blaze_durable::Read::Present:blaze_durable::Read::Error;
  }
  bool writeSlot(uint8_t slot,const uint8_t* bytes,size_t count) override {
    if(slot>1||!mounted_||!bytes||count!=blaze_durable::RECORD_BYTES)return false;
    // Keep the other slot intact; if power fails during this write, recovery
    // fails closed on a torn slot instead of replaying an acknowledged coin.
    File f=LittleFS.open(fileName(slot),"w");
    if(!f)return false;
    const size_t written=f.write(bytes,count);
    f.flush();
    f.close();
    return written==count;
  }
};
