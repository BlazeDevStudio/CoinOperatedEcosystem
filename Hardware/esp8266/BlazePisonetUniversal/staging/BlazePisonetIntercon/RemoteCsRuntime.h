#pragma once
// Stage 5 Remote CS: PisoWiFi controller owns sessions, money and rates.
// NodeMCU owns a strictly bounded, signed coin-window + durable pulse receipt.
// Not the JuanFi MikroTik API; this is a new BLAZE backend adapter contract.
// Every ESP reboot disables D7 until AP-only physical reconciliation.
static const uint32_t REMOTE_MAX_WINDOW_MS=60000UL;
static const uint32_t REMOTE_BURST_QUIET_US=650000UL;
bool remoteWindowActive=false;
bool remoteFrozen=false;
bool remoteHardLocked=false;
uint64_t remoteWindowSession=0;
uint32_t remoteWindowExpires=0;
uint32_t remoteUnresolvedPulses=0;

bool remoteWindowValid(){
 return remoteWindowActive && remoteWindowSession &&
        (int32_t)(millis()-remoteWindowExpires)<0;
}
bool remoteCsGateReady(){
 return interconPref.role==INTERCON_REMOTE && interconConfigHealthy &&
        interconPref.staEnabled && WiFi.status()==WL_CONNECTED &&
        peerPairReady && remoteJournalHealthy && !remoteJournalWriteFailed &&
        interconMasterArmPrepared && !interconMasterArmGuardFailed &&
        csEnabled && !remoteFrozen && !remoteHardLocked &&
        remoteRecord.pendingEvent==0 && remoteWindowValid();
}
void remoteCsTick(){
 if(interconPref.role!=INTERCON_REMOTE)return;
 // A lost Wi-Fi association, unhealthy journal, peer revocation or power
 // quarantine TERMINATES the lease. Rejoining Wi-Fi must NOT reopen D7
 // unless the router sends a fresh signed OPEN on the recovered connection.
 if(remoteWindowActive &&
    (!remoteWindowValid() || !interconPref.staEnabled ||
     WiFi.status()!=WL_CONNECTED || !remoteJournalHealthy ||
     remoteJournalWriteFailed || !peerPairReady || remoteFrozen ||
     remoteHardLocked || !interconMasterArmPrepared)){
  remoteWindowActive=false; // stop hardware immediately; never auto-resume after Wi-Fi loss
  interconRefreshCoinGate();
 }
}
void remoteCsDrainCoin(bool force){
 if(interconPref.role!=INTERCON_REMOTE)return;
 uint8_t queued=0;uint32_t edge=0;
 noInterrupts();queued=coinQueued;edge=lastAcceptedPulseUs;interrupts();
 if(!queued)return;
 if(!force && (uint32_t)(micros()-edge)<REMOTE_BURST_QUIET_US)return;
 noInterrupts();queued=coinQueued;coinQueued=0;interrupts();
 if(!queued)return;
 // Freeze the hardware BEFORE attempting flash writes.
 remoteFrozen=true;remoteWindowActive=false;
 interconRefreshCoinGate();
 if(!remoteJournalHealthy||remoteHardLocked||remoteRecord.pendingEvent||
    !remoteWindowSession||queued>20||remoteRecord.eventCounter==UINT64_MAX){
  remoteHardLocked=true;remoteUnresolvedPulses+=queued;
  Serial.println(F("[REMOTE-CS] CRITICAL: coin pulses require operator reconciliation"));
  return;
 }
 blaze_remote::Record next=remoteRecord;
 next.eventCounter++;
 next.pendingEvent=next.eventCounter;
 next.pendingSession=remoteWindowSession;
 next.pendingPulses=queued;
 if(!remoteCommit(next)){
  remoteHardLocked=true;remoteUnresolvedPulses+=queued;
  Serial.println(F("[REMOTE-CS] CRITICAL: pulse journal failure, D7 locked"));
  return;
 }
 remoteFrozen=false; // pending event itself keeps the gate closed
 Serial.printf("[REMOTE-CS] Durable event %lu pulses=%u; awaiting PisoWiFi ACK\n",
  (unsigned long)(next.pendingEvent&0xFFFFFFFFUL),(unsigned)queued);
}
void remoteCsSendReply(const char* kind){
 blaze_remote::Message response={};
 memcpy(response.kind,kind,5);
 response.source=ESP.getChipId();response.destination=peerPair.peerChip;
 response.command=remoteRecord.lastCommand;
 response.session=remoteRecord.pendingEvent?remoteRecord.pendingSession:
    (remoteCsGateReady()?remoteWindowSession:0ULL); // EMPT proves D7 is actually authorized, not merely a stale lease
 response.event=remoteRecord.pendingEvent;
 response.value=(uint16_t)remoteRecord.pendingPulses;
 char buf[blaze_remote::WIRE_MAX]={};
 const size_t n=blaze_remote::encode(response,peerPair.key,buf);
 if(!n){server.send(503,"text/plain","Signing failure");return;}
 server.sendHeader("Cache-Control","no-store");
 server.send(200,"text/plain",String(buf).substring(0,n));
}
void remoteCsControl(){
 if(interconPref.role!=INTERCON_REMOTE || !interconConfigHealthy ||
    !peerPairReady||!interconPref.staEnabled ||
    WiFi.status()!=WL_CONNECTED||!remoteJournalHealthy){
  server.send(503,"text/plain","Remote CS not configured or journal unhealthy");return;
 }
 IPAddress permitted;
 if(!permitted.fromString(peerPair.peerIp) ||
    server.client().remoteIP()!=permitted ||
    server.client().localIP()==WiFi.softAPIP()){
  server.send(403,"text/plain","Unapproved PisoWiFi controller");return;
 }
 const String frame=server.arg("frame");
 if(frame.length()<130||frame.length()>=blaze_remote::WIRE_MAX){
  server.send(400,"text/plain","Invalid frame length");return;
 }
 blaze_remote::Message request={};
 if(!blaze_remote::decode(frame.c_str(),frame.length(),peerPair.key,
             peerPair.peerChip,ESP.getChipId(),request)){
  server.send(403,"text/plain","Unauthenticated or malformed frame");return;
 }
 if(!strcmp(request.kind,"POLL")){
  // Read-only: safe to retry, and no flash wear from frequent controller polling.
  if(request.session||request.event||request.value){
   server.send(400,"text/plain","POLL fields must be zero");return;
  }
  remoteCsSendReply(remoteRecord.pendingEvent?"EVNT":"EMPT");return;
 }
 // OPEN/CLOS/ACKN consume durable monotonic commands; replay never opens D7.
 if(!request.command || request.command<=remoteRecord.lastCommand){
  server.send(409,"text/plain","Replayed or out-of-order command");return;
 }
 if(!strcmp(request.kind,"OPEN")){
  bool buffered=false;
  noInterrupts();buffered=coinQueued>0 || coinPulseStartUs!=0;interrupts();
  if(buffered || !request.session||request.event||request.value<5||
     request.value>60 || remoteRecord.pendingEvent || remoteHardLocked ||
     remoteFrozen || !interconMasterArmPrepared || interconMasterArmGuardFailed ||
     !csEnabled || (remoteWindowValid() && remoteWindowSession!=request.session)){
   server.send(409,"text/plain","CS closed, occupied, or not physically reconciled");return;
  }
  blaze_remote::Record next=remoteRecord;next.lastCommand=request.command;
  if(!remoteCommit(next)){
   remoteHardLocked=true;interconRefreshCoinGate();
   server.send(503,"text/plain","OPEN command journal commit failed");return;
  }
  remoteWindowSession=request.session;
  remoteWindowExpires=millis()+(uint32_t)request.value*1000UL;
  remoteWindowActive=true;
  interconRefreshCoinGate();
  remoteCsSendReply("OKAY");return;
 }
 if(!strcmp(request.kind,"CLOS")){
  if(!request.session || request.event || request.value ||
     request.session!=remoteWindowSession){
   server.send(409,"text/plain","No matching remote session");return;
  }
  remoteWindowActive=false;interconRefreshCoinGate();
  // Do NOT truncate a multi-pulse denomination on an early close request.
  uint8_t buffered=0;uint32_t edge=0;uint32_t pulseStart=0;
  noInterrupts();buffered=coinQueued;edge=lastAcceptedPulseUs;
  pulseStart=coinPulseStartUs;interrupts();
  if(pulseStart || (buffered && (uint32_t)(micros()-edge)<REMOTE_BURST_QUIET_US)){
   server.send(409,"text/plain","Coin pulse burst settling; retry CLOS / POLL");return;
  }
  remoteCsDrainCoin(false);
  if(remoteHardLocked){
   server.send(503,"text/plain","Uncertain physical coin pulses");return;
  }
  blaze_remote::Record next=remoteRecord;next.lastCommand=request.command;
  if(!remoteCommit(next)){
   remoteHardLocked=true;server.send(503,"text/plain","CLOS journal failed");return;
  }
  remoteCsSendReply(remoteRecord.pendingEvent?"EVNT":"OKAY");return;
 }
 if(!strcmp(request.kind,"ACKN")){
  if(!request.session||request.event==0||remoteRecord.pendingEvent!=request.event||
     remoteRecord.pendingSession!=request.session ||
     remoteRecord.pendingPulses!=request.value){
   server.send(409,"text/plain","Receipt does not match durable pending event");return;
  }
  blaze_remote::Record next=remoteRecord;
  next.lastCommand=request.command;
  next.pendingEvent=0;next.pendingSession=0;next.pendingPulses=0;
  if(!remoteCommit(next)){
   remoteHardLocked=true;server.send(503,"text/plain","ACK journal failed");return;
  }
  remoteWindowActive=false;remoteWindowSession=0;
  interconRefreshCoinGate();
  remoteCsSendReply("OKAY");return;
 }
 server.send(400,"text/plain","Controller may send OPEN, CLOS, ACKN or POLL only");
}
