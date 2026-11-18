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
check('return csEnabled && interconPref.role==INTERCON_STANDARD;' in peer,
      "physical coin route fails closed for Master/Slave stage 1")
check('if (!interconLocalCoinsAllowed()) return;' in source,
      "coin pulse processing rejects non-Standard physical input")
check('coinInputAllowed = interconLocalCoinsAllowed();' in source,
      "boot and manual CS gate respect current role")
check('digitalWrite(CS_ENABLE_PIN, (interconLocalCoinsAllowed() == csActiveHigh)' in source,
      "hardware coin acceptor output follows safe role gate")
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
print("PASS: Stage 1 static contract checks complete (NOT a paid-coin acceptance test)")
