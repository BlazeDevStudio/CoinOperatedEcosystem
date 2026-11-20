#!/usr/bin/env python3
"""Stage 5.1 router adapter fault tests: mock network, REAL sqlite journal.

NOT real OpenWrt/ESP hardware tests. They prove fail-closed signature handling,
stable backend retry nonce, durable acknowledgement ordering and session binding.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

_root=Path(__file__).resolve().parents[1]
_tools=(_root/"Tools") if (_root/"Tools"/"remote_cs_client.py").is_file() else (_root/"tools")
sys.path.insert(0,str(_tools))
from remote_cs_router_bridge import (
    Bridge, BridgeError, Config, DurableState, RouterV1,
    event_backend_nonce, session_token, sha256_join,
    vendo_coin_signature, vendo_poll_signature, vendo_request_signature,
)


class FakeRouter:
    def __init__(self):
        self.target = "A1B2C3D4E5F67890"
        self.expires = 2000000000
        self.insert = True
        self.calls = []
        self.credited_nonces = set()
        self.drop_reply_once = False

    def poll(self):
        return dict(insert=self.insert,target=self.target,expires=self.expires)

    def coin(self,nonce,target,pulses):
        self.calls.append((nonce,target,pulses))
        if not self.insert or target != self.target or pulses not in range(1,21):
            raise BridgeError("no matching router window")
        duplicate=nonce in self.credited_nonces
        self.credited_nonces.add(nonce)
        if self.drop_reply_once:
            self.drop_reply_once=False
            raise BridgeError("router credited; HTTP response LOST")
        return dict(
            duplicate=duplicate,
            credited=0 if duplicate else pulses*100,
            total=pulses*100,
            signature=hashlib.sha256((nonce+target).encode()).hexdigest(),
        )


class FakeEsp:
    def __init__(self):
        self.session=0
        self.pending=()
        self.lastseq=0
        self.history=[]
        self.reject_ack=False

    def poll(self):
        if self.pending:
            session,event,pulses=self.pending
            return dict(kind="EVNT",session=session,event=event,pulses=pulses,command=self.lastseq)
        return dict(kind="EMPT",session=self.session,event=0,pulses=0,command=self.lastseq)

    def command(self,kind,command,session=0,event=0,pulses=0):
        self.history.append((kind,command,session,event,pulses))
        if kind=="POLL":
            return self.poll()
        if command<=self.lastseq:
            raise BridgeError("replayed command")
        self.lastseq=command
        if kind=="OPEN":
            if self.pending:raise BridgeError("pending event")
            self.session=session
            return dict(kind="OKAY",session=session,event=0,pulses=0,command=command)
        if kind=="CLOS":
            if session!=self.session:raise BridgeError("wrong session")
            self.session=0
            return dict(kind="OKAY",session=0,event=0,pulses=0,command=command)
        if kind=="ACKN":
            if self.reject_ack:raise BridgeError("lost ack response")
            if self.pending!=(session,event,pulses):raise BridgeError("wrong pending event")
            self.pending=()
            self.session=0
            return dict(kind="OKAY",session=0,event=0,pulses=0,command=command)
        raise AssertionError(kind)

    def emit(self,pulses=2,event=1):
        assert self.session and not self.pending
        self.pending=(self.session,event,pulses)
        self.session=0 # sample model immediately closes coin window
        return self.pending


class BridgeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=str(Path(self.tmp.name)/"bridge.sqlite3")
        self.cfg=Config("http://192.168.4.50","http://192.168.4.1:4455/blazepwifi/cgi-bin/vendo",
            0x00ABC123,0xA0000001,"remote_vendo_01",bytes(range(1,33)),
            "test-vendo-secret-key-32-long-text",self.path,paid_lab=True)
        self.cfg.validate()
        self.db=DurableState(self.path)
        self.addCleanup(self.db.close)
        self.router=FakeRouter()
        self.esp=FakeEsp()
        self.bridge=Bridge(self.cfg,self.db,self.router,self.esp)

    def open(self):
        result=self.bridge.tick(now=self.router.expires-40)
        self.assertIn("OPENED",result)
        self.assertEqual(len(self.esp.history),1)
        self.assertEqual(self.esp.history[0][0],"OPEN")
        return self.esp.session

    def test_open_credit_ack_and_immutable_nonce(self):
        session=self.open()
        self.esp.emit(pulses=3,event=9)
        result=self.bridge.tick(now=self.router.expires-35)
        self.assertIn("ACKED",result)
        nonce=event_backend_nonce(self.cfg.esp_id,session,9)
        self.assertEqual(self.router.calls,[(nonce,self.router.target,3)])
        self.assertEqual(len(self.router.credited_nonces),1)
        receipt=self.db.conn.execute("SELECT state FROM receipts WHERE event='0000000000000009'").fetchone()
        self.assertEqual(receipt,("acked",))
        self.assertEqual(self.db.pending(self.cfg.esp_id),[])
        self.assertIn("OPENED",self.bridge.tick(now=self.router.expires-30))
        self.assertNotEqual(self.esp.session,0)

    def test_router_response_lost_retries_exact_event_once(self):
        session=self.open()
        self.esp.emit(pulses=2,event=4)
        self.router.drop_reply_once=True
        with self.assertRaisesRegex(BridgeError,"response LOST"):
            self.bridge.tick(now=self.router.expires-20)
        self.assertEqual(self.db.pending(self.cfg.esp_id)[0][-1],"seen")
        self.assertEqual(len(self.router.credited_nonces),1)
        result=self.bridge.tick(now=self.router.expires-18)
        self.assertIn("ACKED",result)
        self.assertEqual(len(self.router.calls),2)
        self.assertEqual(self.router.calls[0],self.router.calls[1])
        self.assertEqual(len(self.router.credited_nonces),1)
        self.assertEqual(self.db.pending(self.cfg.esp_id),[])

    def test_router_credited_then_ack_lost_does_not_repeat_money(self):
        session=self.open()
        self.esp.emit(pulses=1,event=6)
        self.esp.reject_ack=True
        with self.assertRaisesRegex(BridgeError,"lost ack"):
            self.bridge.tick(now=self.router.expires-20)
        self.assertEqual(self.db.pending(self.cfg.esp_id)[0][-1],"credited")
        self.assertEqual(len(self.router.calls),1)
        self.esp.reject_ack=False
        self.assertIn("ACKED",self.bridge.tick(now=self.router.expires-19))
        self.assertEqual(len(self.router.calls),1) # no second backend coin call

    def test_empty_after_lost_ack_response_settles_only_credited(self):
        self.open()
        self.esp.emit(pulses=1,event=7)
        self.esp.reject_ack=True
        with self.assertRaises(BridgeError):
            self.bridge.tick(now=self.router.expires-20)
        # ESP really processed ACK, but HTTP response was lost.
        self.esp.pending=()
        self.esp.session=0
        self.esp.reject_ack=False
        result=self.bridge.tick(now=self.router.expires-18)
        self.assertIn("OPENED",result)
        self.assertEqual(len(self.router.calls),1)
        self.assertEqual(self.db.pending(self.cfg.esp_id),[])

    def test_fail_no_unknown_session_payment(self):
        self.esp.pending=(0x11223344,1,2)
        with self.assertRaisesRegex(BridgeError,"unknown/expired customer session"):
            self.bridge.tick(now=self.router.expires-20)
        self.assertEqual(self.router.calls,[])

    def test_fail_expired_backend_target_holds_event(self):
        self.open()
        self.esp.emit(pulses=2,event=3)
        with self.assertRaisesRegex(BridgeError,"target expired"):
            self.bridge.tick(now=self.router.expires+1)
        self.assertEqual(self.router.calls,[])
        self.assertEqual(self.db.pending(self.cfg.esp_id)[0][-1],"seen")

    def test_uncredited_event_disappears_cannot_reopen(self):
        self.open()
        self.esp.emit(pulses=2,event=4)
        self.router.drop_reply_once=True
        with self.assertRaises(BridgeError):self.bridge.tick(now=self.router.expires-25)
        self.esp.pending=()
        with self.assertRaisesRegex(BridgeError,"lost an uncredited"):
            self.bridge.tick(now=self.router.expires-23)
        self.assertEqual(len(self.esp.history),1)

    def test_backend_window_closed_closes_esp(self):
        self.open()
        self.router.insert=False
        self.assertIn("CLOSED",self.bridge.tick(now=self.router.expires-12))
        self.assertEqual(self.esp.session,0)

    def test_dry_run_makes_no_hardware_or_money_writes(self):
        dry=Config(**{**vars(self.cfg),"paid_lab":False})
        bridge=Bridge(dry,self.db,self.router,self.esp)
        self.assertIn("DRY-RUN",bridge.tick(now=self.router.expires-25))
        self.assertFalse(self.esp.history)
        self.assertFalse(self.router.calls)

    def test_forged_router_coin_confirmation_never_acknowledged(self):
        class Forged(RouterV1):
            def _request(self,*_):
                return {"ok":True,"rental":False,"duplicate":False,
                    "credited_cents":200,"credit_cents":200,
                    "target_nonce":self.expected_target,
                    "response_sig":"f"*64}
        router=Forged(self.cfg);router.expected_target=self.router.target
        with self.assertRaisesRegex(BridgeError,"signed router paid receipt"):
            router.coin("a"*32,self.router.target,2)

    def test_signed_router_poll_verification(self):
        class Stub(RouterV1):
            def _request(self,action,nonce,*_):
                assert action=="poll"
                target="A1B2C3D4E5F67890";expiry=2000000000
                return {"ok":True,"insert":1,"target_nonce":target,
                    "expires":expiry,
                    "controller":{"enabled":1,"coin_enabled":1},
                    "response_sig":vendo_poll_signature(self.cfg.vendo_key,
                              self.cfg.vendo_id,nonce,1,target,expiry)}
        self.assertTrue(Stub(self.cfg).poll()["insert"])
        class Forged(Stub):
            def _request(self,*args):
                out=super()._request(*args);out["response_sig"]="0"*64;return out
        with self.assertRaisesRegex(BridgeError,"router poll signature"):
            Forged(self.cfg).poll()

    def test_unverified_controller_flags_refuse_open(self):
        class Forged(RouterV1):
            def _request(self,action,nonce,*_):
                target="A1B2C3D4E5F67890";expiry=self.expected_expiry
                return {"ok":True,"insert":1,"target_nonce":target,
                    "expires":expiry,
                    "controller":{"enabled":1,"coin_enabled":0},
                    "response_sig":vendo_poll_signature(self.cfg.vendo_key,
                              self.cfg.vendo_id,nonce,1,target,expiry)}
        router=Forged(self.cfg);router.expected_expiry=self.router.expires
        with self.assertRaisesRegex(BridgeError,"coin enable is not authorized"):
            router.poll()

    def test_rejected_signature_cannot_persist_credit_or_ack(self):
        self.open()
        self.esp.emit(pulses=3,event=12)
        class InvalidPaid(FakeRouter):
            def coin(self,*_):
                raise BridgeError("invalid or absent signed router paid receipt")
        bad=InvalidPaid();bad.target=self.router.target;bad.expires=self.router.expires
        bridge=Bridge(self.cfg,self.db,bad,self.esp)
        with self.assertRaisesRegex(BridgeError,"signed router paid receipt"):
            bridge.tick(now=self.router.expires-20)
        self.assertEqual(self.db.pending(self.cfg.esp_id)[0][-1],"seen")
        self.assertFalse(any(x[0]=="ACKN" for x in self.esp.history))

    def test_v1_exact_shell_signature_vectors(self):
        secret="KEY-SECURE-1234567890"
        expected=hashlib.sha256(
            b"KEY-SECURE-1234567890|coin|remote1|0123456789ABCDEF|2|ABCD1234|KEY-SECURE-1234567890"
        ).hexdigest()
        self.assertEqual(vendo_request_signature(secret,"coin","remote1",
                         "0123456789ABCDEF",2,"ABCD1234"),expected)
        self.assertEqual(vendo_coin_signature(secret,"remote1","AAAAAAAAAAAAAAAA",
                     False,200,1200,"ABCD1234"),
            sha256_join(secret,"coin","remote1","AAAAAAAAAAAAAAAA",
                        "false",200,1200,"ABCD1234",secret))
        self.assertEqual(session_token(self.cfg.remote_key,"v1","ABCDEF1234567890"),
                         session_token(self.cfg.remote_key,"v1","abcdef1234567890"))

    def test_db_rejects_payload_collision_and_replay(self):
        session=self.open()
        nonce=event_backend_nonce(self.cfg.esp_id,session,8)
        self.assertEqual(self.db.observe(self.cfg.esp_id,8,session,2,nonce),"seen")
        with self.assertRaisesRegex(BridgeError,"identity reused"):
            self.db.observe(self.cfg.esp_id,8,session,3,nonce)
        with self.assertRaisesRegex(BridgeError,"older remote coin receipt"):
            self.db.observe(self.cfg.esp_id,9,session,2,
                      event_backend_nonce(self.cfg.esp_id,session,9))

    def test_v1_rental_backend_refused_without_esp_ack(self):
        class Rental(RouterV1):
            def _request(self,*_):
                return {"ok":True,"rental":True,"duplicate":False}
        with self.assertRaisesRegex(BridgeError,"unsupported"):
            Rental(self.cfg).coin("A"*16,self.router.target,1)

if __name__=="__main__":
    unittest.main(verbosity=2)
