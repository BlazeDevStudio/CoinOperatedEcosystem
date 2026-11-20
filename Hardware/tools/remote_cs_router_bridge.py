#!/usr/bin/env python3
"""BLAZE INTERCON Stage 5.1 — REAL-API PisoWiFi Remote CS lab bridge.

Standalone Python sidecar for a trusted LAN. Connects the Stage 5 ESP8266
BLZCS1 HMAC endpoint to the ALREADY EXISTING first-party OpenWrt
/cgi-bin/vendo?action=poll|coin API. No new hotspot ledger, rate engine,
fake coin responses, JuanFi endpoints or source edits to Pisowifi/.

Safety: NOT production approved. Existing PisoWiFi v1 accounting and physical
power-cut/flash tests are still NO-GO. Active writes require --enable-paid-lab.
Always fail closed; never send ESP ACKN before signed backend coin confirmation
and a durable local receipt of that confirmation.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from remote_cs_client import send as esp_send

HEX = re.compile(r"^[0-9a-fA-F]+$")
VENDO_ID = re.compile(r"^[A-Za-z0-9._-]{1,48}$")
PROTOCOL_MAX_RESPONSE = 16384
WINDOW_MIN_SEC = 5
WINDOW_MAX_SEC = 60
CLOCK_SAFETY_SEC = 3
MAX_PULSES = 20


class BridgeError(RuntimeError):
    """Unsafe, malformed or inconclusive state. Never ACK a coin on error."""


@dataclass(frozen=True)
class Config:
    esp_url: str
    vendo_url: str
    esp_id: int
    controller_id: int
    vendo_id: str
    remote_key: bytes
    vendo_key: str
    db_path: str
    paid_lab: bool = False
    timeout: float = 5.0

    def validate(self) -> None:
        if not (0 < self.esp_id <= 0xFFFFFFFF and
                0 < self.controller_id <= 0xFFFFFFFF and
                self.esp_id != self.controller_id):
            raise BridgeError("invalid ESP or controller IDs")
        if len(self.remote_key) != 32 or not VENDO_ID.fullmatch(self.vendo_id):
            raise BridgeError("invalid pairing key or vendo ID")
        if len(self.vendo_key) < 16 or len(self.vendo_key) > 256 or "|" in self.vendo_key:
            raise BridgeError("router vendo secret must be private, strong and without pipes")
        for url in (self.esp_url, self.vendo_url):
            parts = urlsplit(url)
            if parts.scheme != "http" or not parts.hostname or parts.username or parts.password:
                raise BridgeError("only plain HTTP to a pinned, trusted local IPv4 endpoint is supported")
            try:
                address = ipaddress.IPv4Address(parts.hostname)
            except ipaddress.AddressValueError as exc:
                raise BridgeError("use explicit pinned IPv4, not DNS hostnames or WAN URLs") from exc
            if (not (address.is_private or address.is_loopback) or
                    address.is_multicast or address.is_unspecified):
                raise BridgeError("WAN/public/controller multicast address refused")
            if parts.fragment or parts.query:
                raise BridgeError("endpoint URL must not contain a query or fragment")
        if self.timeout <= 0 or self.timeout > 30:
            raise BridgeError("network timeout must be 0–30 seconds")


def sha256_join(*parts: object) -> str:
    """Existing OpenWrt v1 legacy signature, NOT HMAC; mirror its shell printf."""
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def vendo_request_signature(secret: str, action: str, vendo_id: str,
                            nonce: str, pulses: int, target: str) -> str:
    return sha256_join(secret, action, vendo_id, nonce, pulses, target, secret)


def vendo_poll_signature(secret: str, vendo_id: str, nonce: str,
                         insert: int, target: str, expires: int) -> str:
    return sha256_join(secret, "poll", vendo_id, nonce, insert, target, expires, secret)


def vendo_coin_signature(secret: str, vendo_id: str, nonce: str,
                         duplicate: bool, credited: int, total: int, target: str) -> str:
    return sha256_join(secret, "coin", vendo_id, nonce,
                       "true" if duplicate else "false", credited, total, target, secret)


def session_token(remote_key: bytes, vendo_id: str, target: str) -> int:
    """Stable explicit router-target-to-ESP session64 mapping, never IP-derived."""
    if not 8 <= len(target) <= 32 or not HEX.fullmatch(target):
        raise BridgeError("invalid signed router target nonce")
    digest = hmac.new(remote_key,
        ("BLZCS1-SESSION|"+vendo_id+"|"+target.lower()).encode("ascii"),
        hashlib.sha256).digest()
    token = int.from_bytes(digest[:8], "big")
    if not token:
        raise BridgeError("invalid derived session ID")
    return token


def event_backend_nonce(esp_id: int, session: int, event: int) -> str:
    """One fixed v1 nonce for all retries of the *same* physical event."""
    if not (esp_id and session and event):
        raise BridgeError("invalid physical event identity")
    return hashlib.sha256(
        f"BLZCS1-COIN|{esp_id:08X}|{session:016X}|{event:016X}".encode()
    ).hexdigest()[:32]


def exact_unsigned(obj: dict, name: str, maximum: int = 0x7FFFFFFF) -> int:
    value = obj.get(name)
    if type(value) is not int or value < 0 or value > maximum:
        raise BridgeError("invalid signed router "+name)
    return value


def parse_json_response(raw: bytes) -> dict:
    if not raw or len(raw) > PROTOCOL_MAX_RESPONSE:
        raise BridgeError("router response length invalid")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise BridgeError("malformed router JSON") from exc
    if not isinstance(result, dict):
        raise BridgeError("router JSON response must be an object")
    if result.get("ok") is not True:
        raise BridgeError("router refused request: "+str(result.get("error", "unknown"))[:120])
    return result


class RouterV1:
    """Exact first-party OpenWrt v1 signature; use only the dedicated vendo port."""

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def _request(self, action: str, nonce: str, pulses: int = 0, target: str = "") -> dict:
        args = {
            "action": action, "id": self.cfg.vendo_id, "nonce": nonce,
            "pulses": str(pulses), "target": target,
            "sig": vendo_request_signature(self.cfg.vendo_key, action,
                                            self.cfg.vendo_id, nonce, pulses, target),
        }
        glue = "&" if "?" in self.cfg.vendo_url else "?"
        url = self.cfg.vendo_url + glue + urlencode(args)
        req = Request(url, method="GET", headers={"Cache-Control": "no-store"})
        try:
            with urlopen(req, timeout=self.cfg.timeout) as response:
                data = response.read(PROTOCOL_MAX_RESPONSE + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise BridgeError("router network/read failed; payment status UNKNOWN") from exc
        return parse_json_response(data)

    def poll(self) -> dict:
        nonce = secrets.token_hex(16)
        j = self._request("poll", nonce)
        insert = exact_unsigned(j, "insert", 1)
        target = j.get("target_nonce")
        if not isinstance(target, str) or (target and
             (len(target) < 8 or len(target) > 32 or not HEX.fullmatch(target))):
            raise BridgeError("invalid signed router target")
        expires = exact_unsigned(j, "expires", 0x7FFFFFFFFFFFFFFF)
        signature = j.get("response_sig")
        if not isinstance(signature, str) or len(signature) != 64:
            raise BridgeError("missing signed router poll proof")
        expected = vendo_poll_signature(self.cfg.vendo_key, self.cfg.vendo_id,
                                        nonce, insert, target, expires)
        if not hmac.compare_digest(signature, expected):
            raise BridgeError("invalid router poll signature")
        if insert and (not target or expires <= 0):
            raise BridgeError("router advertised invalid active target")
        controller = j.get("controller")
        if insert:
            if not isinstance(controller, dict) or (
                controller.get("enabled") != 1 or controller.get("coin_enabled") != 1
            ):
                raise BridgeError("router controller's coin enable is not authorized")
        return {"insert": bool(insert), "target": target, "expires": expires}

    def coin(self, nonce: str, target: str, pulses: int) -> dict:
        if not (8 <= len(nonce) <= 32 and HEX.fullmatch(nonce) and
                8 <= len(target) <= 32 and HEX.fullmatch(target) and
                1 <= pulses <= MAX_PULSES):
            raise BridgeError("invalid router coin request fields")
        j = self._request("coin", nonce, pulses, target)
        if j.get("rental") is True:
            raise BridgeError("rental coin target unsupported by this hotspot-only adapter")
        duplicate = j.get("duplicate")
        if type(duplicate) is not bool:
            raise BridgeError("invalid signed coin duplicate flag")
        credited = exact_unsigned(j, "credited_cents")
        total = exact_unsigned(j, "credit_cents")
        if j.get("target_nonce") != target or (
            duplicate and credited != 0
        ) or (not duplicate and credited <= 0):
            raise BridgeError("invalid router coin credit / target / duplicate")
        sig = j.get("response_sig")
        expected = vendo_coin_signature(self.cfg.vendo_key,self.cfg.vendo_id,
                                        nonce,duplicate,credited,total,target)
        if not isinstance(sig, str) or not hmac.compare_digest(sig,expected):
            raise BridgeError("invalid or absent signed router paid receipt")
        return {"duplicate":duplicate,"credited":credited,"total":total,"signature":sig}


class DurableState:
    """Persistent event mapping and monotonic command sequence; never erase on boot."""

    def __init__(self, file_path: str):
        p = Path(file_path)
        if p.is_symlink():
            raise BridgeError("SQLite path must not be a symlink")
        if not p.parent.is_dir():
            raise BridgeError("database parent directory does not exist")
        if p.exists() and (not p.is_file() or p.stat().st_mode & 0o077):
            raise BridgeError("existing bridge DB must be an owner-only regular file (0600)")
        if not p.exists():
            fd = os.open(str(p), os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
            os.close(fd)
        self.conn = sqlite3.connect(str(p), timeout=5, isolation_level=None)
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.execute("PRAGMA journal_mode=DELETE")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS sequences(esp_id INTEGER PRIMARY KEY, last INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS windows(
            esp_id INTEGER NOT NULL, session TEXT NOT NULL,
            target TEXT NOT NULL, vendo_id TEXT NOT NULL, expires INTEGER NOT NULL,
            PRIMARY KEY(esp_id,session), UNIQUE(esp_id,vendo_id,target));
        CREATE TABLE IF NOT EXISTS receipts(
            esp_id INTEGER NOT NULL, event TEXT NOT NULL, session TEXT NOT NULL,
            pulses INTEGER NOT NULL, nonce TEXT NOT NULL, state TEXT NOT NULL
                CHECK(state IN ('seen','credited','acked')),
            signed_proof TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(esp_id,event));
        """)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _write(self, sql: str, params=()):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur
        except BaseException:
            self.conn.rollback()
            raise

    def sequence(self, esp_id: int) -> int:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute("SELECT last FROM sequences WHERE esp_id=?", (esp_id,)).fetchone()
            value = (row[0] if row else 0) + 1
            if value >= 2**63:
                raise BridgeError("remote command sequence exhausted")
            self.conn.execute("INSERT INTO sequences(esp_id,last) VALUES(?,?) "
                 "ON CONFLICT(esp_id) DO UPDATE SET last=excluded.last", (esp_id,value))
            self.conn.commit()
            return value
        except BaseException:
            self.conn.rollback()
            raise

    def bind_window(self, esp_id: int, session: int, target: str,
                    vendo_id: str, expires: int) -> None:
        sid = f"{session:016X}"
        existing = self.conn.execute(
            "SELECT target,vendo_id,expires FROM windows WHERE esp_id=? AND session=?",
            (esp_id,sid)).fetchone()
        if existing:
            if existing != (target,vendo_id,expires):
                raise BridgeError("router changed persisted session mapping or expiry")
            return
        try:
            self._write("INSERT INTO windows VALUES(?,?,?,?,?)",
                        (esp_id,sid,target,vendo_id,expires))
        except sqlite3.IntegrityError as exc:
            raise BridgeError("duplicate router target bound to another session") from exc

    def window(self, esp_id: int, session: int):
        return self.conn.execute(
            "SELECT target,vendo_id,expires FROM windows WHERE esp_id=? AND session=?",
            (esp_id,f"{session:016X}")).fetchone()

    def pending(self, esp_id: int):
        return self.conn.execute(
            "SELECT event,session,pulses,nonce,state FROM receipts "
            "WHERE esp_id=? AND state!='acked' ORDER BY rowid", (esp_id,)).fetchall()

    def observe(self, esp_id: int, event: int, session: int, pulses: int, nonce: str) -> str:
        eid,sid=f"{event:016X}",f"{session:016X}"
        if not self.window(esp_id,session):
            raise BridgeError("unknown customer session; do not guess router target")
        other=self.pending(esp_id)
        if any(row[0]!=eid for row in other):
            raise BridgeError("an older remote coin receipt remains unresolved")
        row=self.conn.execute("SELECT session,pulses,nonce,state FROM receipts "
                 "WHERE esp_id=? AND event=?", (esp_id,eid)).fetchone()
        if row:
            if row[:3] != (sid,pulses,nonce) or row[3]=="acked":
                raise BridgeError("ESP event identity reused or already settled")
            return row[3]
        self._write("INSERT INTO receipts(esp_id,event,session,pulses,nonce,state) "
                    "VALUES(?,?,?,?,?,'seen')", (esp_id,eid,sid,pulses,nonce))
        return "seen"

    def credited(self, esp_id: int, event: int, signature: str):
        eid=f"{event:016X}"
        self._write("UPDATE receipts SET state='credited',signed_proof=? "
                    "WHERE esp_id=? AND event=? AND state='seen'",
                    (signature,esp_id,eid))
        row=self.conn.execute("SELECT state,signed_proof FROM receipts "
                  "WHERE esp_id=? AND event=?", (esp_id,eid)).fetchone()
        if not row or row != ("credited",signature):
            raise BridgeError("backend proof could not be durably preserved")

    def acked(self, esp_id: int, event_hex: str) -> None:
        self._write("UPDATE receipts SET state='acked' WHERE esp_id=? "
                    "AND event=? AND state='credited'", (esp_id,event_hex))


class RemoteController:
    def __init__(self, cfg: Config):
        self.cfg=cfg

    def poll(self) -> dict:
        return self.command("POLL",0)

    def command(self, kind: str, command: int, session: int=0,
                event: int=0, pulses: int=0) -> dict:
        try:
            return esp_send(self.cfg.esp_url,self.cfg.remote_key,
                            self.cfg.controller_id,self.cfg.esp_id,kind,command,
                            session,event,pulses)
        except (HTTPError, URLError, ValueError, OSError, TimeoutError) as exc:
            raise BridgeError("ESP command failed, physical state UNKNOWN: "+kind) from exc


class Bridge:
    def __init__(self, cfg: Config, store: DurableState,
                 router: RouterV1 | None = None,
                 esp: RemoteController | None = None):
        self.cfg=cfg
        self.store=store
        self.router=router or RouterV1(cfg)
        self.esp=esp or RemoteController(cfg)

    def _mutate(self, kind: str, session: int=0, event: int=0, value: int=0) -> dict:
        if not self.cfg.paid_lab:
            raise BridgeError("paid operations disabled; require --enable-paid-lab")
        seq=self.store.sequence(self.cfg.esp_id)
        return self.esp.command(kind,seq,session,event,value)

    def tick(self, now: int | None = None) -> str:
        now=int(time.time()) if now is None else now
        esp=self.esp.poll()
        if esp["kind"] not in ("EVNT","EMPT"):
            raise BridgeError("ESP returned unexpected POLL result")
        if esp["kind"]=="EVNT":
            session,event,pulses=esp["session"],esp["event"],esp["pulses"]
            if not session or not event or not 1 <= pulses <= MAX_PULSES:
                raise BridgeError("ESP signed invalid coin event")
            mapped=self.store.window(self.cfg.esp_id,session)
            if not mapped:
                raise BridgeError("ESP reported unknown/expired customer session; manual reconciliation")
            target,vendo_id,expires=mapped
            if vendo_id!=self.cfg.vendo_id:
                raise BridgeError("payment event for a different vendo")
            nonce=event_backend_nonce(self.cfg.esp_id,session,event)
            if not self.cfg.paid_lab:
                return "DRY-RUN: event pending, no credit or ACK sent"
            state=self.store.observe(self.cfg.esp_id,event,session,pulses,nonce)
            if state=="seen":
                if now>=expires:
                    raise BridgeError("router target expired before verified credit; HOLD event for reconciliation")
                proof=self.router.coin(nonce,target,pulses)
                self.store.credited(self.cfg.esp_id,event,proof["signature"])
            receipt=self.esp.command("POLL",0)
            if receipt["kind"]!="EVNT" or any(receipt[k]!=esp[k] for k in ("session","event","pulses")):
                raise BridgeError("ESP event changed after backend credit; HOLD for reconciliation")
            reply=self._mutate("ACKN",session,event,pulses)
            if reply["kind"]!="OKAY" or reply["event"] or reply["pulses"]:
                raise BridgeError("ESP returned invalid ACK receipt")
            self.store.acked(self.cfg.esp_id,f"{event:016X}")
            return f"ACKED: physical ESP event {event:016X}, {pulses} pulses; router signed credit recorded"

        # EMPTY is a signed device statement. A previously committed router
        # credit might have had an ACK response lost during a reboot.
        outstanding=self.store.pending(self.cfg.esp_id)
        if outstanding:
            if any(row[4]!="credited" for row in outstanding):
                raise BridgeError("ESP lost an uncredited observed event; operator reconciliation")
            if self.cfg.paid_lab:
                for event_hex,*_ in outstanding:
                    self.store.acked(self.cfg.esp_id,event_hex)
            else:
                return "DRY-RUN: previous credited receipt awaiting confirmation"

        router=self.router.poll()
        if esp["event"] or esp["pulses"]:
            raise BridgeError("invalid empty ESP receipt")
        if not router["insert"]:
            if esp["session"] and self.cfg.paid_lab:
                reply=self._mutate("CLOS",esp["session"])
                if reply["kind"] not in ("OKAY","EVNT"):
                    raise BridgeError("ESP refused CLOS")
                return "CLOSED: router coin window no longer available"
            return "IDLE: no active signed PisoWiFi coin window"

        target,expires=router["target"],router["expires"]
        token=session_token(self.cfg.remote_key,self.cfg.vendo_id,target)
        if esp["session"] and esp["session"]!=token:
            if self.cfg.paid_lab:
                reply=self._mutate("CLOS",esp["session"])
                if reply["kind"] not in ("OKAY","EVNT"):
                    raise BridgeError("ESP refused mismatched CLOS")
            return "CLOSED: ESP still bound to different customer session"

        # Never bind a new target while a previous event is unresolved.
        self.store.bind_window(self.cfg.esp_id,token,target,self.cfg.vendo_id,expires)
        if esp["session"]==token:
            return "ACTIVE: signed router target matches ESP coin window"
        lease=min(WINDOW_MAX_SEC,expires-now-CLOCK_SAFETY_SEC)
        if lease<WINDOW_MIN_SEC:
            return "CLOSED: router window too close to expiry to accept coins"
        if not self.cfg.paid_lab:
            return f"DRY-RUN: would open physical CS for {lease}s (no writes sent)"
        reply=self._mutate("OPEN",token,0,lease)
        if reply["kind"]!="OKAY" or reply["session"]!=token:
            raise BridgeError("ESP did not confirm requested coin window")
        return f"OPENED: signed customer session {token:016X} for {lease}s"


def run() -> int:
    p=argparse.ArgumentParser(description="BLAZE Stage5.1 PisoWiFi v1 coin bridge — LAB NO-GO")
    p.add_argument("--esp-url",required=True,help="pinned NodeMCU local HTTP URL")
    p.add_argument("--vendo-url",required=True,help="full dedicated-port /cgi-bin/vendo URL")
    p.add_argument("--esp-id",required=True,help="8 uppercase HEX ESP chip ID")
    p.add_argument("--controller-id",required=True,help="8 uppercase HEX controller ID")
    p.add_argument("--vendo-id",required=True,help="existing OpenWrt vendo ID (max 48 chars)")
    p.add_argument("--db",required=True,help="persistent private SQLite 0600 path")
    p.add_argument("--enable-paid-lab",action="store_true",help="actually open CS/credit/ACK; still NO-GO")
    p.add_argument("--loop",action="store_true",help="repeat until killed; default is one pass")
    p.add_argument("--interval",type=float,default=1.0,help="poll interval >= 0.5sec")
    args=p.parse_args()
    if args.interval<0.5 or args.interval>30:
        raise BridgeError("poll interval must be 0.5–30s")
    def hex_id(name: str, raw: str) -> int:
        if len(raw)!=8 or not re.fullmatch(r"[0-9A-F]{8}",raw):
            raise BridgeError(name+" requires 8 uppercase HEX digits")
        return int(raw,16)
    key=os.environ.get("BLAZE_REMOTE_CS_KEY","")
    secret=os.environ.get("BLAZE_VENDO_KEY","")
    if not re.fullmatch(r"[0-9A-Fa-f]{64}",key):
        raise BridgeError("set BLAZE_REMOTE_CS_KEY in environment to 32 random bytes hex")
    cfg=Config(args.esp_url,args.vendo_url,hex_id("ESP",args.esp_id),
      hex_id("controller",args.controller_id),args.vendo_id,bytes.fromhex(key),
      secret,args.db,paid_lab=args.enable_paid_lab)
    cfg.validate()
    with DurableState(cfg.db_path) as state:
        bridge=Bridge(cfg,state)
        while True:
            print(bridge.tick(),flush=True)
            if not args.loop:break
            time.sleep(args.interval)
    return 0


if __name__=="__main__":
    try:
        sys.exit(run())
    except (BridgeError,sqlite3.DatabaseError,OSError) as exc:
        print("REMOTE CS BRIDGE HALTED:",exc,file=sys.stderr)
        sys.exit(1)
