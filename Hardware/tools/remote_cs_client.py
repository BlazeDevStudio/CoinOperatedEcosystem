#!/usr/bin/env python3
"""Reference PisoWiFi controller transport for BLAZE Stage 5 Remote CS.

NOT an accounting engine. No money/time/voucher grants occur here.
A real controller must commit (device,event)->customer credit transaction before
sending ACKN. This CLI never acknowledges automatically after POLL.
Requires Python 3 standard library; shop-local trusted HTTP network only.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

KINDS={"OPEN","CLOS","ACKN","POLL","EVNT","EMPT","OKAY"}
FRAME_FIELDS=9

def parse_hex(name:str,value:str,digits:int)->int:
    if len(value)!=digits or any(c not in "0123456789ABCDEF" for c in value):
        raise ValueError(f"{name} must be {digits} uppercase hexadecimal digits")
    return int(value,16)

def sign_frame(key:bytes,kind:str,source:int,destination:int,command:int,
               session:int,event:int,value:int)->str:
    if len(key)!=32 or kind not in KINDS or any(x<0 or x>0xFFFFFFFFFFFFFFFF for x in (command,session,event)):
        raise ValueError("invalid frame parameter")
    if not (0<source<=0xFFFFFFFF and 0<destination<=0xFFFFFFFF) or not 0<=value<=65535:
        raise ValueError("invalid endpoint or value")
    prefix=f"BLZCS1|{kind}|{source:08X}|{destination:08X}|{command:016X}|{session:016X}|{event:016X}|{value}|"
    return prefix+hmac.new(key,prefix.encode("ascii"),hashlib.sha256).hexdigest().upper()

def verify_frame(wire:str,key:bytes,source:int,destination:int)->dict:
    chunks=wire.strip().split("|")
    if len(chunks)!=FRAME_FIELDS or chunks[0]!="BLZCS1" or chunks[1] not in KINDS:
        raise ValueError("malformed response")
    if not hmac.compare_digest(
        hmac.new(key,("|".join(chunks[:8])+"|").encode("ascii"),hashlib.sha256).hexdigest().upper(),
        chunks[8]):
        raise ValueError("invalid response HMAC")
    src=parse_hex("response source",chunks[2],8)
    dst=parse_hex("response destination",chunks[3],8)
    if src!=source or dst!=destination:
        raise ValueError("response bound to wrong controller/device")
    for name,part in zip(("command","session","event"),chunks[4:7]):
        parse_hex(name,part,16)
    if not chunks[7].isdigit() or (len(chunks[7])>1 and chunks[7][0]=="0"):
        raise ValueError("invalid response value")
    value=int(chunks[7])
    if value>65535:raise ValueError("value out of range")
    return {
        "kind":chunks[1],"command":int(chunks[4],16),
        "session":int(chunks[5],16),"event":int(chunks[6],16),
        "pulses":value,
    }

def reserve_command(db_path:str,device:int)->int:
    """Persist sequence BEFORE sending so a crash cannot replay a mutating command."""
    with sqlite3.connect(db_path,timeout=15) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS sequences(device INTEGER PRIMARY KEY, last INTEGER NOT NULL)")
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("SELECT last FROM sequences WHERE device=?",(device,)).fetchone()
        seq=(row[0] if row else 0)+1
        # SQLite signed 64-bit; sufficient for many years of controller operations.
        if seq>=2**63:raise RuntimeError("sequence exhausted")
        conn.execute("INSERT INTO sequences(device,last) VALUES(?,?) "
                     "ON CONFLICT(device) DO UPDATE SET last=excluded.last",(device,seq))
        conn.commit()
        return seq

def send(base:str,key:bytes,controller:int,device:int,kind:str,seq:int,
         session:int=0,event:int=0,value:int=0)->dict:
    wire=sign_frame(key,kind,controller,device,seq,session,event,value)
    endpoint=base.rstrip("/")+"/api/pisowifi/control"
    req=urllib.request.Request(endpoint,
        data=urllib.parse.urlencode({"frame":wire}).encode("ascii"),
        headers={"Content-Type":"application/x-www-form-urlencoded"},
        method="POST")
    with urllib.request.urlopen(req,timeout=5) as response:
        reply=response.read(256).decode("ascii").strip()
    return verify_frame(reply,key,device,controller)

def main()->int:
    p=argparse.ArgumentParser(description="BLAZE Remote CS LAB transport; NO automatic credit")
    p.add_argument("--esp",required=True,help="NodeMCU STA URL, e.g. http://192.168.1.70")
    p.add_argument("--controller",required=True,help="8-digit uppercase HEX PisoWiFi controller ID")
    p.add_argument("--device",required=True,help="8-digit uppercase HEX ESP chip ID (zero padded)")
    p.add_argument("--db",default="./blaze-remote-seq.sqlite3",help="persistent router command counter database")
    p.add_argument("action",choices=["open","close","poll","ack"])
    p.add_argument("--session",default="0000000000000000",help="16-digit uppercase HEX customer session token")
    p.add_argument("--event",default="0000000000000000",help="16-digit uppercase HEX event ID from POLL")
    p.add_argument("--pulses",type=int,default=0,help="exact pulse count when ACKing after durable backend credit")
    p.add_argument("--seconds",type=int,default=30,help="open lease in seconds, 5..60")
    args=p.parse_args()
    key_text=os.environ.get("BLAZE_REMOTE_CS_KEY","")
    if len(key_text)!=64:raise ValueError("set BLAZE_REMOTE_CS_KEY to 64 uppercase HEX characters")
    key=bytes.fromhex(key_text)
    controller=parse_hex("controller",args.controller,8)
    device=parse_hex("device",args.device,8)
    session=parse_hex("session",args.session,16)
    event=parse_hex("event",args.event,16)
    if not controller or not device or controller==device:raise ValueError("bad IDs")
    kind={"open":"OPEN","close":"CLOS","poll":"POLL","ack":"ACKN"}[args.action]
    value=args.seconds if kind=="OPEN" else args.pulses if kind=="ACKN" else 0
    if kind=="OPEN" and (not session or event or not 5<=value<=60):raise ValueError("OPEN needs nonzero session, no event and 5–60 seconds")
    if kind=="ACKN" and (not session or not event or not 1<=value<=20):raise ValueError("ACK needs exact nonzero session/event/pulses")
    if kind in ("POLL","CLOS") and (event or (kind=="POLL" and session)):
        raise ValueError("POLL is zero session/event; CLOS has zero event")
    seq=0 if kind=="POLL" else reserve_command(args.db,device)
    result=send(args.esp,key,controller,device,kind,seq,session,event,value)
    print(f"RESPONSE {result['kind']} session={result['session']:016X} "
          f"event={result['event']:016X} physical_pulses={result['pulses']}")
    if result["kind"]=="EVNT":
        print("DO NOT ACK until your REAL PisoWiFi backend has durably credited "
              "(device,event) exactly once to the correct customer.")
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (ValueError,urllib.error.URLError,RuntimeError) as exc:
        print("REMOTE CS ERROR:",exc,file=sys.stderr);sys.exit(1)
