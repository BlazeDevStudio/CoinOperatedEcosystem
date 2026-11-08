"""Host simulation only: never flashes or claims an OpenWrt device was tested."""
import concurrent.futures
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'openwrt/bin/blazerentalctl'
CGI = ROOT / 'openwrt/cgi-bin/blazerental'
LIB = ROOT / 'openwrt/lib/core.sh'


class StandaloneApi(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'state'
        self.env = os.environ.copy()
        self.env.update(BLAZERENTAL_STATE_DIR=str(self.state), BLAZERENTAL_LIB=str(LIB), LC_ALL='C')
        self.cmd('init')

    def cmd(self, *args, check=True):
        cp = subprocess.run(['sh', str(CLI), *args], capture_output=True, text=True, env=self.env)
        if check and cp.returncode != 0:
            self.fail(f'Command {args} failed: {cp.stderr}')
        return cp

    def pair(self):
        out = dict(line.split('=', 1) for line in self.cmd('register').stdout.splitlines())
        self.assertRegex(out['device_id'], r'^[0-9a-f]{24}$')
        self.assertRegex(out['device_secret'], r'^[0-9a-f]{64}$')
        return out

    def api(self, id, secret, nonce='deadbeef00112233deadbeef00112233', sig=None):
        mac = hmac.new(bytes.fromhex(secret), f'v1|status|{id}|{nonce}'.encode(), hashlib.sha256).hexdigest()
        query=f'action=status&device_id={id}&nonce={nonce}&sig={mac if sig is None else sig}'
        e = self.env | {'REQUEST_METHOD': 'GET', 'QUERY_STRING': query}
        cp = subprocess.run(['sh', str(CGI)], capture_output=True, text=True, env=e)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout.split('\r\n\r\n', 1)[-1].split('\n\n', 1)[-1])

    def test_shell_syntax_and_clean_structure(self):
        for p in [CLI, CGI, LIB, ROOT / 'openwrt/install.sh']:
            self.assertEqual(subprocess.run(['sh', '-n', str(p)]).returncode, 0)
            contents=p.read_text()
            self.assertNotIn('/etc/blazepwifi-', contents)
            self.assertNotIn('/cgi-bin/rental-admin', contents)

    def test_register_and_authentic_reply(self):
        info = self.pair()
        r = self.api(info['device_id'], info['device_secret'])
        self.assertTrue(r['ok'])
        self.assertEqual(r['device_id'], info['device_id'])
        self.assertEqual(r['api_version'], 1)
        canonical = f"v1|status-reply|{r['device_id']}|{r['nonce']}|{r['server_time']}|{r['lease_until']}"
        expect = hmac.new(bytes.fromhex(info['device_secret']), canonical.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(r['proof'], expect)
        self.assertFalse(self.api(info['device_id'], info['device_secret'], sig='0'*64)['ok'])
        self.assertFalse(self.api('f'*24, info['device_secret'])['ok'])

    def test_grant_replay_and_conflict(self):
        info=self.pair();did=info['device_id'];key=info['device_secret']
        tx='receipt_20261108_a1'
        first=self.cmd('grant',did,'600',tx).stdout
        self.assertIn('replayed=false',first)
        once=int(dict(line.split('=') for line in first.splitlines())['lease_until'])
        second=self.cmd('grant',did,'600',tx).stdout
        self.assertIn('replayed=true',second)
        self.assertEqual(int(dict(line.split('=') for line in second.splitlines())['lease_until']),once)
        self.assertNotEqual(self.cmd('grant',did,'300',tx,check=False).returncode,0)
        self.assertNotEqual(self.cmd('grant','f'*24,'300','new_receipt_12',check=False).returncode,0)
        self.assertEqual(sum(1 for l in (self.state/'state.tsv').read_text().splitlines() if l.startswith('R\t')),1)
        r=self.api(did,key)
        self.assertEqual(r['lease_until'],once)

    def test_concurrent_retry_is_single_credit(self):
        info=self.pair();did=info['device_id'];tx='collision_concurrent_1'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self.cmd,'grant',did,'900',tx) for _ in range(2)]
            results=[f.result().stdout for f in futures]
        self.assertCountEqual(['replayed=false','replayed=true'],[re.search(r'replayed=(?:true|false)',x).group(0) for x in results])
        self.assertEqual(sum(1 for l in (self.state/'state.tsv').read_text().splitlines() if l.startswith('R\t')),1)

    def test_corruption_fails_closed(self):
        info=self.pair()
        with open(self.state/'state.tsv','a') as f:f.write('BAD\tevil\n')
        self.assertNotEqual(self.cmd('grant',info['device_id'],'60','bad_payload_0123',check=False).returncode,0)
        self.assertFalse(self.api(info['device_id'],info['device_secret'])['ok'])

    def test_missing_crypto_does_not_generate_poor_entropy(self):
        info=self.pair()
        bogus=self.cmd('grant',info['device_id'],'0','bad_range_12345',check=False)
        self.assertNotEqual(bogus.returncode,0)


class JavaProtocol(unittest.TestCase):
    def test_java_hmac_interop(self):
        with tempfile.TemporaryDirectory() as td:
            main = ROOT/'android/app/src/main/java/com/blazesystems/blazerental/ProtocolV1.java'
            harness = ROOT/'tests/ProtocolV1Harness.java'
            cp = subprocess.run(['javac','-d',td,str(main),str(harness)],capture_output=True,text=True)
            if cp.returncode:self.fail(cp.stderr)
            run = subprocess.run(['java','-cp',td,'ProtocolV1Harness'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('JAVA_PROTOCOL_PASS',run.stdout)

if __name__=='__main__':unittest.main()
