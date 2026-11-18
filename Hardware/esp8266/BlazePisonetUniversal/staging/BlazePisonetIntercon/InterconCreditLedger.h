#pragma once
// BLAZE INTERCON v2: portable transaction rules for future remote coin credit.
// REVIEW ONLY; no live ESP8266 timer or CS output calls these functions.
// Durability contract: commit() must atomically persist the ENTIRE resulting
// snapshot (sequence + remaining balance + count) before ACK or RAM mutation.
// An EEPROM write and separate dedupe-file write do NOT meet this contract.
#include <stdint.h>
namespace blaze_credit {
static const uint64_t MAX_UNITS=604800ULL*100000ULL; // 7 days, 0.01 ms units
struct Event {
  uint32_t issuer;
  uint64_t sequence;      // monotonically increasing and persisted by Master
  uint16_t seconds;       // signed by Master in BLZ2 CRED envelope
};
struct Snapshot {
  uint32_t authorizedIssuer;
  uint64_t lastSequence;
  uint64_t remainingUnits;
  uint32_t paidEventCount;
  uint16_t lastSeconds;
};
enum class Outcome : uint8_t {
  Applied, Duplicate, OutOfOrder, WrongIssuer, Conflict, Overflow, NotDurable
};
using CommitFn=bool (*)(const Snapshot&,void*);
inline Outcome prepare(const Snapshot& s,const Event& e,Snapshot& next){
  if(!e.issuer||e.issuer!=s.authorizedIssuer)return Outcome::WrongIssuer;
  if(!e.sequence||!e.seconds)return Outcome::Conflict;
  if(e.sequence<s.lastSequence)return Outcome::Duplicate;
  if(e.sequence==s.lastSequence)
    return e.seconds==s.lastSeconds?Outcome::Duplicate:Outcome::Conflict;
  if(s.lastSequence==UINT64_MAX || e.sequence!=s.lastSequence+1)
    return Outcome::OutOfOrder;
  const uint64_t extra=(uint64_t)e.seconds*100000ULL;
  if(s.remainingUnits>MAX_UNITS || extra>MAX_UNITS-s.remainingUnits ||
     s.paidEventCount==UINT32_MAX)return Outcome::Overflow;
  next=s;
  next.lastSequence=e.sequence;
  next.remainingUnits+=extra;
  next.paidEventCount++;
  next.lastSeconds=e.seconds;
  return Outcome::Applied;
}
inline Outcome apply(Snapshot& inRam,const Event& e,CommitFn commit,void* ctx){
  Snapshot candidate={};
  const Outcome decision=prepare(inRam,e,candidate);
  if(decision!=Outcome::Applied)return decision;
  if(!commit||!commit(candidate,ctx))return Outcome::NotDurable;
  inRam=candidate;
  return Outcome::Applied;
}
// The Master must keep exactly one outstanding unpaid/unacknowledged event.
// Only the identical sequence and content may be retried after ACK loss.
struct MasterPending {
  uint64_t lastIssued;
  uint64_t pendingSequence;
  uint16_t pendingSeconds;
};
inline bool stage(MasterPending& state,uint16_t seconds,
                  bool (*commit)(const MasterPending&,void*),void* ctx){
  if(!seconds||state.pendingSequence||state.lastIssued==UINT64_MAX||!commit)
    return false;
  MasterPending next=state;
  next.lastIssued++;
  next.pendingSequence=next.lastIssued;
  next.pendingSeconds=seconds;
  if(!commit(next,ctx))return false;
  state=next;
  return true;
}
inline bool settle(MasterPending& state,uint64_t acked,
                   bool (*commit)(const MasterPending&,void*),void* ctx){
  if(!acked||acked!=state.pendingSequence||!commit)return false;
  MasterPending next=state;
  next.pendingSequence=0;next.pendingSeconds=0;
  if(!commit(next,ctx))return false;
  state=next;
  return true;
}
} // namespace blaze_credit
