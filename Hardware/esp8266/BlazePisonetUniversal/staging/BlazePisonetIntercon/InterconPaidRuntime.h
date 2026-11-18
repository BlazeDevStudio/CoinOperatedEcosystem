#pragma once
// BLAZE INTERCON Stage 4 — one paired Master -> one paired Slave.
// The Slave's journal, NOT its V1.5 EEPROM shadow, is the authority for
// remotely credited time and its replay receipt. A durable grant is committed
// before updating outputs/timer or transmitting ACKN.
// PROTOTYPE / HARDWARE NO-GO: paid coin input must be characterized on the
// actual coin acceptor. ESP power loss between electrical pulse and first
// successful journal commit cannot be solved by firmware alone.
#include "InterconCreditLedger.h"

static const uint32_t INTERCON_TIMER_CHECKPOINT_MS=60000UL;
static const uint32_t INTERCON_PENDING_RETRY_MS=2500UL;
bool interconMasterFlowHalted=false;
uint32_t interconUnresolvedPulseCount=0;
uint32_t interconLastPendingSend=0;
uint32_t interconLastCheckpoint=0;
uint32_t interconAppliedCredits=0;
uint32_t interconRejectedCredits=0;

bool interconJournalHealthy(){
  return interconJournalFsReady && interconJournalPairReady &&
         !interconJournalWriteFailed &&
         interconRecovered.status==blaze_journal::Status::Healthy;
}
bool interconMasterReady(){
  return interconPref.role==INTERCON_MASTER && interconConfigHealthy &&
         interconJournalHealthy() && peerPairReady && peerOnline() &&
         interconPref.staEnabled && WiFi.status()==WL_CONNECTED &&
         !interconMasterFlowHalted && csEnabled &&
         interconRecovered.snapshot.master.pendingSequence==0 &&
         addMinutes*60UL+addSeconds>0 &&
         addMinutes*60UL+addSeconds<=65535UL;
}
bool interconSlaveReady(){
  return interconPref.role==INTERCON_SLAVE && interconConfigHealthy &&
         interconJournalHealthy() && peerPairReady &&
         interconPref.staEnabled && WiFi.status()==WL_CONNECTED;
}
void interconRefreshCoinGate(){
  const bool enabled=interconLocalCoinsAllowed();
  if(!enabled){
    noInterrupts();coinInputAllowed=false;interrupts();
    writeCsEnable();
  }else{
    writeCsEnable();
    noInterrupts();coinInputAllowed=true;interrupts();
  }
}
bool interconJournalSetBalance(uint64_t units){
  if(interconPref.role!=INTERCON_SLAVE || !interconJournalHealthy() ||
     units>blaze_credit::MAX_UNITS)return false;
  if(interconRecovered.snapshot.slave.remainingUnits==units)return true;
  blaze_journal::Record target=interconRecovered.snapshot;
  target.slave.remainingUnits=units;
  return interconJournalCommit(target);
}
bool interconMasterCommit(const blaze_credit::MasterPending& state,void*){
  if(!interconJournalHealthy() || interconPref.role!=INTERCON_MASTER)
    return false;
  blaze_journal::Record target=interconRecovered.snapshot;
  target.master=state;
  return interconJournalCommit(target);
}
bool interconSlaveCommit(const blaze_credit::Snapshot& state,void*){
  if(!interconJournalHealthy() || interconPref.role!=INTERCON_SLAVE)
    return false;
  blaze_journal::Record target=interconRecovered.snapshot;
  target.slave=state; // Receipt, paid balance, count and seq in ONE flash image
  return interconJournalCommit(target);
}
void interconMasterSendPending(){
  if(interconPref.role!=INTERCON_MASTER || !interconJournalHealthy() ||
     !peerPairReady || !peerOnline() || WiFi.status()!=WL_CONNECTED)return;
  const blaze_credit::MasterPending& p=interconRecovered.snapshot.master;
  if(!p.pendingSequence || !p.pendingSeconds)return;
  IPAddress peer;
  if(!peer.fromString(peerPair.peerIp))return;
  blaze_peer::Frame frame={};
  memcpy(frame.kind,"CRED",5);
  frame.source=ESP.getChipId();
  frame.destination=peerPair.peerChip;
  frame.eventHigh=(uint32_t)(p.pendingSequence>>32);
  frame.eventLow=(uint32_t)p.pendingSequence;
  frame.units=p.pendingSeconds;
  peerSend(frame,peer);
  interconLastPendingSend=millis();
}
void interconMasterTick(){
  if(interconPref.role!=INTERCON_MASTER ||
     !interconJournalHealthy())return;
  const blaze_credit::MasterPending& p=interconRecovered.snapshot.master;
  if(!p.pendingSequence)return;
  if(interconLastPendingSend==0 ||
     (uint32_t)(millis()-interconLastPendingSend)>=INTERCON_PENDING_RETRY_MS)
    interconMasterSendPending();
}
void interconMasterReceiveCoin(uint8_t count){
  if(!count || interconPref.role!=INTERCON_MASTER)return;
  // Freeze the physical CS before committing an entire bounded pulse burst.
  // A multi-pulse denomination is ONE durable event for count * secondsPerPulse.
  interconMasterFlowHalted=true;
  interconRefreshCoinGate();
  if(!interconConfigHealthy || !interconJournalHealthy() ||
     !peerPairReady || !interconPref.staEnabled ||
     interconRecovered.snapshot.master.pendingSequence){
    interconUnresolvedPulseCount+=count;
    Serial.println(F("[INTERCON] CRITICAL: paid burst without free journal slot"));
    return;
  }
  const uint32_t secondsPerPulse=(uint32_t)addMinutes*60UL+addSeconds;
  const uint32_t grant=secondsPerPulse*(uint32_t)count;
  if(!secondsPerPulse || count>20 || !grant || grant>65535UL){
    interconUnresolvedPulseCount+=count;
    Serial.println(F("[INTERCON] CRITICAL: burst rejected; operator reconciliation required"));
    return;
  }
  blaze_credit::MasterPending current=interconRecovered.snapshot.master;
  if(!blaze_credit::stage(current,(uint16_t)grant,
                          interconMasterCommit,nullptr)){
    interconUnresolvedPulseCount+=count;
    Serial.println(F("[INTERCON] CRITICAL: journal commit failed; payment quarantined"));
    return;
  }
  interconMasterFlowHalted=false; // pending event itself keeps physical CS OFF
  interconMasterSendPending(); // EXACTLY the committed burst, not RAM coins
  interconRefreshCoinGate(); // OFF until durable, authenticated ACK
}
// Coin acceptors can emit several pulses for one denomination. Wait for a
// quiet interval so the whole electrical burst becomes one durable event.
// Actual pulse widths and spacing require bench calibration before payment GO.
void interconMasterDrainCoin(bool force){
  if(interconPref.role!=INTERCON_MASTER)return;
  uint8_t count=0;
  noInterrupts();
  const uint32_t lastEdge=lastAcceptedPulseUs;
  const uint8_t queued=coinQueued;
  interrupts();
  if(!queued)return;
  if(!force && (uint32_t)(micros()-lastEdge)<650000UL)return;
  noInterrupts();
  count=coinQueued;coinQueued=0;
  interrupts();
  if(count)interconMasterReceiveCoin(count);
}
void interconSlaveSendAck(uint64_t sequence){
  if(!peerPairReady || !peerOnline())return;
  IPAddress dest;
  if(!dest.fromString(peerPair.peerIp))return;
  blaze_peer::Frame ack={};
  memcpy(ack.kind,"ACKN",5);
  ack.source=ESP.getChipId();ack.destination=peerPair.peerChip;
  ack.eventHigh=(uint32_t)(sequence>>32);
  ack.eventLow=(uint32_t)sequence;
  ack.units=0;
  peerSend(ack,dest);
}
void interconHandleCredit(const blaze_peer::Frame& frame){
  if(!interconSlaveReady() || !peerOnline() || frame.units==0)return;
  // Before a new transaction, settle any elapsed countdown in RAM. The
  // next single journal write includes BOTH that debit and the new grant.
  updateTimerState();
  if(!interconJournalHealthy())return;
  const uint64_t sequence=((uint64_t)frame.eventHigh<<32)|frame.eventLow;
  blaze_credit::Event credit={frame.source,sequence,frame.units};
  blaze_credit::Snapshot updated=interconRecovered.snapshot.slave;
  updated.remainingUnits=remainingMs100;
  const blaze_credit::Outcome result=
    blaze_credit::apply(updated,credit,interconSlaveCommit,nullptr);
  if(result==blaze_credit::Outcome::Duplicate){
    // Same seq/seconds already durable: receipt can safely be resent
    // without adding another second or duplicating a paid sale.
    if(sequence==interconRecovered.snapshot.slave.lastSequence &&
       frame.units==interconRecovered.snapshot.slave.lastSeconds)
      interconSlaveSendAck(sequence);
    return;
  }
  if(result!=blaze_credit::Outcome::Applied){
    if(interconRejectedCredits<UINT32_MAX)interconRejectedCredits++;
    Serial.printf("[INTERCON] CREDIT refused: %d\n",(int)result);
    return;
  }
  // Exactly one durable grant: apply to live timer ONLY after commit.
  remainingMs100=updated.remainingUnits;
  remainingSeconds=(uint32_t)((remainingMs100+99999ULL)/100000ULL);
  timerRunning=remainingMs100>0;
  lastCountdownMillis=millis();
  lastRecoveryCheckpoint=lastCountdownMillis;
  interconLastCheckpoint=lastCountdownMillis;
  setRelays(timerRunning);
  if(timerRunning)onPaidTimeGranted();
  lastCoin=millis();lastNearEndStartedAt=lastCoin;
  stopChime();playCoinChime();
  // Legacy EEPROM is now a redundant UI/config shadow, NEVER recovery
  // authority for Slave. A lost shadow write cannot undo accepted credit.
  savePersistentState();
  if(interconAppliedCredits<UINT32_MAX)interconAppliedCredits++;
  interconSlaveSendAck(sequence);
}
void interconHandleAck(const blaze_peer::Frame& frame){
  if(interconPref.role!=INTERCON_MASTER || !interconJournalHealthy() ||
     !peerPairReady || frame.units!=0)return;
  const uint64_t sequence=((uint64_t)frame.eventHigh<<32)|frame.eventLow;
  blaze_credit::MasterPending pending=interconRecovered.snapshot.master;
  if(!sequence || sequence!=pending.pendingSequence)return;
  if(!blaze_credit::settle(pending,sequence,
                           interconMasterCommit,nullptr)){
    interconMasterFlowHalted=true;
    Serial.println(F("[INTERCON] ACK received but journal settlement failed"));
    return;
  }
  interconLastPendingSend=0;
  interconRefreshCoinGate(); // safe to accept the next coin
}
void interconSlaveRestoreFromJournal(){
  if(interconPref.role!=INTERCON_SLAVE)return;
  // Never use the legacy EEPROM saved paid balance for a Slave: it might
  // lag an accepted remote event or include unrelated Standard-mode data.
  remainingMs100=interconJournalHealthy()?
    interconRecovered.snapshot.slave.remainingUnits:0ULL;
  remainingSeconds=(uint32_t)((remainingMs100+99999ULL)/100000ULL);
  timerRunning=false; // retained paid balance remains paused after reboot
  lastCountdownMillis=millis();
  lastRecoveryCheckpoint=lastCountdownMillis;
  interconLastCheckpoint=lastCountdownMillis;
  setRelays(false);
  if(!interconJournalHealthy())
    Serial.println(F("[INTERCON] Slave journal unavailable: PAID TIME LOCKED"));
  else
    Serial.println(F("[INTERCON] Slave restored authoritative journal balance, paused"));
}
void interconSlaveCheckpoint(){
  if(interconPref.role!=INTERCON_SLAVE || !timerRunning ||
     !interconJournalHealthy())return;
  const uint32_t now=millis();
  if((uint32_t)(now-interconLastCheckpoint)<INTERCON_TIMER_CHECKPOINT_MS)
    return;
  if(!interconJournalSetBalance(remainingMs100)){
    // Financial journal may be unknown. Do not continue the countdown
    // or accept a new remote credit until offline reconciliation.
    timerRunning=false;
    Serial.println(F("[INTERCON] CRITICAL: countdown checkpoint failed"));
    setRelays(false);
    schedulePcShutdown();
    return;
  }
  interconLastCheckpoint=now;
}
