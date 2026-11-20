#!/usr/bin/env python3
"""Stage 5 static wiring contracts: source assertions, NOT physical payment validation."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon"
source=(root/"BlazePisonetIntercon.ino").read_text()
discovery=(root/"InterconDiscovery.h").read_text()
runtime=(root/"RemoteCsRuntime.h").read_text()
journal=(root/"RemoteCsJournal.h").read_text()
checks={
 "fourth role additive": 'INTERCON_REMOTE=3' in discovery and 'INTERCON_STANDARD=0' in discovery,
 "Remote CS GPIO gate dedicated": 'if(interconPref.role==INTERCON_REMOTE)return remoteCsGateReady();' in discovery,
 "no remote local rental credit": 'if(interconPref.role==INTERCON_REMOTE) {\n    remoteCsDrainCoin(false);' in source and 'addCoinTime()' not in runtime,
 "remote timer add rejected": 'INTERCON_MASTER || interconPref.role==INTERCON_REMOTE)return false;' in source,
 "controller HMAC strict": 'blaze_remote::decode(frame.c_str(),frame.length(),peerPair.key' in runtime,
 "controller IP pinned": 'server.client().remoteIP()!=permitted' in runtime,
 "durable anti-replay": 'request.command<=remoteRecord.lastCommand' in runtime and 'next.lastCommand=request.command' in runtime,
 "no flash writes on POLL": 'if(!strcmp(request.kind,"POLL"))' in runtime and 'remoteCsSendReply(remoteRecord.pendingEvent?' in runtime,
 "pending session and event journaled before notice": 'next.pendingSession=remoteWindowSession;' in runtime and 'if(!remoteCommit(next))' in runtime,
 "exact receipt required": 'remoteRecord.pendingEvent!=request.event' in runtime and 'remoteRecord.pendingSession!=request.session' in runtime,
 "on reboot closed": 'bool remoteWindowActive=false;' in runtime and 'bool interconMasterArmPrepared=false;' in (root/"InterconArmGuard.h").read_text(),
 "AP-only initialization": 'server.on("/api/pisowifi/journal/initialize"' in source and 'server.client().localIP()!=WiFi.softAPIP()' in source,
 "no default credentials for arming": 'strcmp(adminPassword,"blaze-admin")==0' in source and 'strcmp(AP_PASSWORD,"12345678")==0' in source,
 "no silent rekey": 'LittleFS.exists(JOURNAL_SLOT0)||LittleFS.exists(JOURNAL_SLOT1)||remoteJournalPresent' in source,
 "original pinout preserved": all(x in source for x in ['uint8_t relayPin = 16;','uint8_t relay2Pin = 12;','CS_ENABLE_PIN = 13;']),
 "window bounded to 5-60s": 'request.value<5' in runtime and 'request.value>60' in runtime,
 "expiry closed": 'remoteCsTick();' in source and 'remoteWindowActive=false; // stop hardware immediately' in runtime,
 "reconnect needs fresh signed OPEN": 'WiFi.status()!=WL_CONNECTED || !remoteJournalHealthy' in runtime and 'remoteCsGateReady()?remoteWindowSession:0ULL' in runtime,
 "CS mode selectable": '<option value="3">Remote CS' in source,
}
for name,valid in checks.items():
 if not valid: raise SystemExit("FAIL: "+name)
 print("PASS: "+name)
