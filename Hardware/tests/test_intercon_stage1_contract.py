#!/usr/bin/env python3
"""Static source contract checks, NOT runtime or hardware validation.

Tests refer to the actual Stage 1 sketch and header. A separate GitHub Actions
job runs the real ESP8266 Arduino compiler. Passing this does not establish
peer payment correctness or safety of connected relays.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKETCH=ROOT/"esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/BlazePisonetIntercon.ino"
PEER=SKETCH.parent/"InterconDiscovery.h"
source=SKETCH.read_text(encoding="utf-8")
peer=PEER.read_text(encoding="utf-8")
JOURNAL=SKETCH.parent/"InterconFlashJournal.h"
CODEC=SKETCH.parent/"InterconJournalCodec.h"
journal=JOURNAL.read_text(encoding="utf-8")
codec=CODEC.read_text(encoding="utf-8")
RUNTIME=SKETCH.parent/"InterconPaidRuntime.h"
PEER_AUTH=SKETCH.parent/"InterconPeerAuth.h"
runtime=RUNTIME.read_text(encoding="utf-8")
peer_auth=PEER_AUTH.read_text(encoding="utf-8")

def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("FAIL: " + message)
    print("PASS:", message)

check(SKETCH.is_file() and PEER.is_file(), "real staging sketch and header exist")
check('WiFi.mode(WIFI_AP_STA);' in source, "AP stays active when STA is enabled")
check('WiFi.mode(WIFI_STA);' not in source, "no STA-only WiFi mode")
check('WiFi.softAP(AP_NAME' in source and 'WiFi.localIP()' in source,
      "AP and LAN-IP access are represented")
check('loadInterconConfig(fsReady);' in source and 'saveInterconConfig()' in source,
      "role/STA settings saved outside legacy EEPROM")
check('INTERCON_STANDARD=0' in peer and 'INTERCON_MASTER=1' in peer and 'INTERCON_SLAVE=2' in peer,
      "Standard is default with explicit Master and Slave roles")
check('if(interconPref.role==INTERCON_STANDARD)return true;' in peer and
      'if(interconPref.role==INTERCON_MASTER)return interconMasterReady();' in peer and
      'return false;' in peer,
      "Standard local coins, Master journal/paired coin gate, Slave closed")
check('if(interconPref.role==INTERCON_MASTER)' in source and
      'interconMasterReceiveCoin(count);' in source and
      'if (!interconLocalCoinsAllowed()) return;' in source,
      "Master pulses journaled, Slave cannot credit local coin pulses")
check('coinInputAllowed = interconLocalCoinsAllowed();' in source,
      "boot and manual CS gate respect current role")
check('digitalWrite(CS_ENABLE_PIN, (interconLocalCoinsAllowed() == csActiveHigh)' in source,
      "hardware coin acceptor output follows safe role gate")
check('interconConfigHealthy=false;' in peer and 'interconPref.role=INTERCON_SLAVE;' in peer,
      "corrupt settings cannot silently enable local coin intake")
check('void interconReceiveDiscovery()' in peer and 'void interconAdvertise()' in peer,
      "bounded UDP discovery is implemented")
check('INTERCON_MAX_PEERS=12' in peer and 'if(slot<0)return;' in peer,
      "untrusted discovery cannot allocate an unbounded peer table")
check('if(len<8 || len>14' in peer, "discovery packets have a strict length limit")
check('COIN_EVENT' not in peer and 'CREDIT|' not in peer and 'addCoinTime()' not in peer,
      "discovery never grants remote paid time")
check('void pulsePowerButton()' in source or 'bool pulsePowerButton()' in source,
      "momentary PWR_SW behavior remains in V1.5")
check('uint8_t relay2Pin = 12;' in source and 'CS_ENABLE_PIN = 13;' in source,
      "owner D6 PWR_SW / D7 CS default GPIOs preserved")
check('uint8_t relayPin = 16;' in source and 'uint8_t displayClk = 5;' in source
      and 'uint8_t displayDio = 4;' in source, "owner cutoff and display pins preserved")
check('X-Blaze-Action' in source and 'server.collectHeaders' in source,
      "CSRF-reducing custom HTTP action header required")
check('server.authenticate("admin",adminPassword)' in source,
      "HTTP Basic administrator auth still used")
check('if(nextStaEnabled && strcmp(adminPassword,"blaze-admin")==0' in source,
      "STA LAN admin disabled until default password is changed")
check('s += F(",\\\"interconPeers\\\":[");' in source,
      "authenticated status includes nearby peer list")
check('s += F(",\\\"staPassword\\\":");' not in source,
      "STA password is never echoed in status JSON")
check('interconJournalRecover(fsReady);' in source,
      "recovery is wired into boot without granting paid time")
check('interconJournalInitialize()' in source and
      '/api/intercon/journal/initialize' in source and 'Journal already exists or storage unavailable' in source,
      "journal initialization requires explicit admin action and refuses existing records")
check('if(interconJournalFsReady &&' in source and
      'LittleFS.exists(JOURNAL_SLOT0)||LittleFS.exists(JOURNAL_SLOT1)' in source,
      "re-pair and role changes cannot silently clear existing journal history")
check('IMAGE_BYTES=92' in codec and 'keyTag[16]' in codec and
      'crc32(out,88)' in codec,
      "canonical 92-byte on-flash images and 128-bit key binding")
check('interconJournalWriteFailed=true' in journal and
      'interconRecovered.status!=blaze_journal::Status::Healthy' in journal,
      "failed or degraded journal prevents further automatic commits")
check('interconSlaveRestoreFromJournal();' in source and
      'interconRecovered.snapshot.slave.remainingUnits' in runtime and
      'remainingMs100=interconJournalHealthy()?' in runtime,
      "Slave restores exclusively from receipt+balance journal, not stale EEPROM")
check('target.slave.remainingUnits=units;' in runtime and
      'return interconJournalCommit(target);' in runtime and
      'interconJournalSetBalance(targetUnits)' in source and
      'interconJournalSetBalance(0)' in source,
      "Slave manual time, reset and expiry atomically update journal")
check('interconSlaveCheckpoint();' in source and
      'INTERCON_TIMER_CHECKPOINT_MS=60000UL' in runtime,
      "Slave countdown checkpoints through same durable journal")
check('blaze_credit::apply(updated,credit,interconSlaveCommit,nullptr)' in runtime and
      'target.slave=state;' in runtime and
      'interconSlaveSendAck(sequence);' in runtime and
      'onPaidTimeGranted();' in runtime,
      "Slave commits credit plus sequence before ACK and PC power request")
check('blaze_credit::stage(current,(uint16_t)seconds,' in runtime and
      'interconMasterCommit,nullptr' in runtime and
      'interconMasterSendPending();' in runtime,
      "Master persists accepted coin event before wireless send")
check('blaze_credit::settle(pending,sequence,' in runtime and
      'interconRefreshCoinGate();' in runtime and
      'interconMasterReady()' in runtime,
      "Master reopens coin slot only after durable authenticated ACK")
check('interconHandleCredit(input);' in peer_auth and
      'interconHandleAck(input);' in peer_auth and
      'blaze_peer::decode' in peer_auth and
      'if(!interconSlaveReady() || !peerOnline()' in runtime,
      "remote commands require signed peer and journal readiness")
check('interconMasterFlowHalted=true;' in runtime and
      'interconUnresolvedPulseCount' in runtime,
      "multiple uncommitted physical pulses trigger visible fail-stop alarm")
check('interconPref.role==INTERCON_SLAVE &&' in source and
      'interconSlaveRestoreFromJournal' in source,
      "Standards and Masters do not inherit Slave paid balances")
check('INTERCON_STANDARD' in peer and 'INTERCON_MASTER' in peer and
      'INTERCON_SLAVE' in peer,
      "all three operator modes remain independently available")
print("PASS: Stage 4 source integration safety checks (hardware validation still required)")
