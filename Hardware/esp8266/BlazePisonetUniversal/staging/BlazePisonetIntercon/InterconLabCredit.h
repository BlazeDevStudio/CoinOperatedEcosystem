#pragma once
// BLAZE INTERCON Stage 4: authenticated JOURNAL-ONLY lab credit exchange.
//
// IMPORTANT: This is NOT a customer-payment mechanism and NOT wired to
// coinInput, remainingMs100, paid sales, cutoff, or motherboard PWR_SW.
// Master/Slave physical coin intake remains disabled. Never promote this
// laboratory endpoint to real-money service without the authoritative timer
// migration, power-cut testing, and independent review.
//
// Include AFTER InterconJournalFS.h and masterJournal/slaveJournal instances.
// Called only from loop/HTTP handlers, not from ISR.
#include <stdint.h>

uint32_t interconLabLastSent=0;
uint32_t interconLabLastReceived=0;
uint32_t interconLabRejected=0;
uint32_t interconLabAcknowledged=0;

inline uint64_t interconLabSeq(const blaze_peer::Frame& p) {
  return ((uint64_t)p.eventHigh<<32)|(uint64_t)p.eventLow;
}
inline blaze_credit::MasterPending interconLabMasterPending() {
  blaze_credit::MasterPending current={};
  if(!masterJournal.hasRecord())return current;
  const blaze_journal::Payload& p=masterJournal.record().p;
  current.lastIssued=p.sequence;
  current.pendingSequence=p.pendingSequence;
  current.pendingSeconds=p.pendingSeconds;
  return current;
}
inline blaze_credit::Snapshot interconLabSlaveSnapshot() {
  blaze_credit::Snapshot result={};
  if(!slaveJournal.hasRecord())return result;
  const blaze_journal::Payload& p=slaveJournal.record().p;
  result.authorizedIssuer=p.issuer;
  result.lastSequence=p.sequence;
  result.remainingUnits=p.remainingUnits;
  result.paidEventCount=p.paidCount;
  result.lastSeconds=p.lastSeconds;
  return result;
}
inline bool interconLabPeerOK(){
  return interconConfigHealthy && peerPairReady && peerOnline() &&
         interconPref.staEnabled && WiFi.status()==WL_CONNECTED &&
         interconFileSystemReady;
}
inline void interconLabSendPending(){
  if(interconPref.role!=INTERCON_MASTER||!interconLabPeerOK()||
     !masterJournal.ready()||!masterJournal.hasRecord()||
     masterJournal.record().p.issuer!=ESP.getChipId())return;
  const blaze_credit::MasterPending p=interconLabMasterPending();
  if(!p.pendingSequence||!p.pendingSeconds || p.pendingSeconds>3600)return;
  IPAddress peerAddress;
  if(!peerAddress.fromString(peerPair.peerIp))return;
  blaze_peer::Frame credit={};
  memcpy(credit.kind,"CRED",5);
  credit.source=ESP.getChipId();
  credit.destination=peerPair.peerChip;
  credit.eventHigh=(uint32_t)(p.pendingSequence>>32);
  credit.eventLow=(uint32_t)p.pendingSequence;
  credit.units=p.pendingSeconds;
  peerSend(credit,peerAddress);
  interconLabLastSent=millis();
}
inline bool interconLabStageTest(uint16_t seconds){
  // No paid coin inputs, live timer, or remote relays touched.
  if(interconPref.role!=INTERCON_MASTER || !interconLabPeerOK() ||
     !masterJournal.ready() || !masterJournal.hasRecord() ||
     masterJournal.record().p.issuer!=ESP.getChipId() ||
     !seconds || seconds>3600 || timerRunning || remainingSeconds ||
     pcShutdownPending || powerPulseActive)return false;
  blaze_credit::MasterPending state=interconLabMasterPending();
  if(!blaze_credit::stage(state,seconds,blaze_journal::commitMasterPending,
                          &masterJournal))return false;
  interconLabSendPending();
  return true;
}
inline void interconLabReceived(const blaze_peer::Frame& frame,IPAddress sourceIP){
  // Peer IP + signed source/destination already validated by PeerAuth.
  IPAddress approved;
  if(!approved.fromString(peerPair.peerIp) || sourceIP!=approved ||
     !interconLabPeerOK() || !frame.source ||
     frame.source!=peerPair.peerChip ||
     frame.destination!=ESP.getChipId())return;
  const uint64_t sequence=interconLabSeq(frame);
  if(!strcmp(frame.kind,"CRED")){
    if(interconPref.role!=INTERCON_SLAVE ||
       !slaveJournal.ready() || !slaveJournal.hasRecord() ||
       slaveJournal.record().p.issuer!=peerPair.peerChip ||
       !sequence || !frame.units || frame.units>3600 ||
       timerRunning || remainingSeconds ||
       pcShutdownPending || powerPulseActive) {
      interconLabRejected++;return;
    }
    blaze_credit::Snapshot shadow=interconLabSlaveSnapshot();
    const blaze_credit::Event event={frame.source,sequence,frame.units};
    const blaze_credit::Outcome outcome=blaze_credit::apply(
      shadow,event,blaze_journal::commitSlaveSnapshot,&slaveJournal);
    // Only acknowledge a DURABLY committed event or an exact repeat of
    // the latest committed event; no ACK for uncertain disk outcomes.
    const bool committed=outcome==blaze_credit::Outcome::Applied;
    const bool duplicate=outcome==blaze_credit::Outcome::Duplicate &&
       sequence==slaveJournal.record().p.sequence &&
       frame.units==slaveJournal.record().p.lastSeconds;
    if(!committed && !duplicate) {
      interconLabRejected++;return;
    }
    IPAddress peerAddress;
    if(!peerAddress.fromString(peerPair.peerIp))return;
    blaze_peer::Frame ack={};
    memcpy(ack.kind,"ACKN",5);
    ack.source=ESP.getChipId();ack.destination=peerPair.peerChip;
    ack.eventHigh=frame.eventHigh;ack.eventLow=frame.eventLow;
    ack.units=0;
    peerSend(ack,peerAddress);
    if(committed)interconLabLastReceived=millis();
    // This is a SHADOW journal. It never starts a paid PC session.
    return;
  }
  if(!strcmp(frame.kind,"ACKN") && interconPref.role==INTERCON_MASTER &&
     masterJournal.ready() && masterJournal.hasRecord() &&
     masterJournal.record().p.issuer==ESP.getChipId() && sequence) {
    blaze_credit::MasterPending pending=interconLabMasterPending();
    if(pending.pendingSequence==sequence && pending.pendingSeconds &&
       blaze_credit::settle(pending,sequence,
                             blaze_journal::commitMasterPending,
                             &masterJournal)){
      interconLabAcknowledged++;
    }
  }
}
inline void interconLabTick(){
  if(interconPref.role!=INTERCON_MASTER||!interconLabPeerOK())return;
  if((uint32_t)(millis()-interconLabLastSent)>=3000UL)
    interconLabSendPending(); // same event ID, no duplicate grants
}
