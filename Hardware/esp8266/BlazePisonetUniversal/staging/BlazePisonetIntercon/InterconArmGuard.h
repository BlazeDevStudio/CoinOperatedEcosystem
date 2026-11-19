#pragma once
// INTERCON Stage 4.1 lab-only Master arm guard.
// RAM starts LOCKED on EVERY ESP boot. Re-arm requires AP-only authenticated
// operator reconciliation, plus this persistent identity-bound marker.
// A previous arm marker is never automatically erased or treated as consent.
#include "InterconArmGuardCodec.h"

static const char* INTERCON_ARM_FILE="/intercon-arm1";
static const char* INTERCON_ARM_TEMP="/intercon-arm1.tmp";
bool interconMasterArmPrepared=false;
bool interconMasterArmGuardFailed=false;

bool interconArmGuardRead(const char* path,
                          const blaze_journal::Binding& expected){
  File f=LittleFS.open(path,"r");
  if(!f)return false;
  uint8_t image[blaze_arm::IMAGE_BYTES]={};
  const bool ok=f.size()==blaze_arm::IMAGE_BYTES &&
                f.read(image,sizeof(image))==(int)sizeof(image);
  f.close();
  return ok && blaze_arm::matches(image,sizeof(image),expected);
}
bool interconArmGuardProvision(){
  // Caller MUST first prove physical CS is disabled, no pending credit and
  // explicit on-AP operator acknowledgment. Never invoke from boot/loop.
  if(interconMasterArmGuardFailed || !interconFileSystemReady ||
     (interconPref.role!=INTERCON_MASTER &&
      interconPref.role!=INTERCON_REMOTE))return false;
  blaze_journal::Binding binding={};
  if(interconPref.role==INTERCON_REMOTE){
    blaze_remote::Record remote={};
    if(!remoteJournalHealthy||!remoteCsBinding(remote))return false;
    binding.owner=remote.owner;binding.peer=remote.controller;
    memcpy(binding.keyTag,remote.keyTag,16);
    binding.role=blaze_journal::ROLE_MASTER; // marker codec, unique remote keyTag
  }else if(!interconJournalFsReady ||
           !interconJournalBinding(binding))return false;
  if(LittleFS.exists(INTERCON_ARM_FILE)){
    if(interconArmGuardRead(INTERCON_ARM_FILE,binding))return true;
    interconMasterArmGuardFailed=true; // mismatch/corrupt marker: hard lock
    return false;
  }
  uint8_t image[blaze_arm::IMAGE_BYTES]={};
  if(!blaze_arm::encode(binding,image))return false;
  if(LittleFS.exists(INTERCON_ARM_TEMP) &&
     !LittleFS.remove(INTERCON_ARM_TEMP)){
    interconMasterArmGuardFailed=true;return false;
  }
  File f=LittleFS.open(INTERCON_ARM_TEMP,"w");
  if(!f){interconMasterArmGuardFailed=true;return false;}
  const size_t written=f.write(image,sizeof(image));
  f.flush();f.close();
  if(written!=sizeof(image) ||
     !interconArmGuardRead(INTERCON_ARM_TEMP,binding) ||
     !LittleFS.rename(INTERCON_ARM_TEMP,INTERCON_ARM_FILE) ||
     !interconArmGuardRead(INTERCON_ARM_FILE,binding)){
    interconMasterArmGuardFailed=true;
    return false; // NEVER clear or overwrite ambiguous persistent evidence
  }
  return true;
}
const char* interconArmGuardStatus(){
  if(interconPref.role!=INTERCON_MASTER && interconPref.role!=INTERCON_REMOTE)return "not-coin-master";
  if(interconMasterArmGuardFailed)return "HARD LOCK: marker storage or binding failure";
  if(!interconMasterArmPrepared)return "BOOT QUARANTINE: reconcile physical coins";
  return "Operator reconciled THIS BOOT";
}
