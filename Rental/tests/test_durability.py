"""Host-only fault injection for the standalone local ledger, NOT flash power-loss certification."""
import concurrent.futures
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'openwrt/bin/blazerentalctl'
LIB = ROOT / 'openwrt/lib/core.sh'
CGI = ROOT / 'openwrt/cgi-bin/blazerental'


class LedgerDurability(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.env = os.environ.copy()
        self.env.update(BLAZERENTAL_STATE_DIR=str(self.state), BLAZERENTAL_LIB=str(LIB), LC_ALL='C')
        self.assertEqual(self.run_cli('init').returncode, 0)
        self.identity = dict(x.split('=', 1) for x in self.run_cli('register').stdout.strip().splitlines())
        self.did = self.identity['device_id']

    def run_cli(self, *args, env=None):
        return subprocess.run(['sh', str(CLI), *args], env=env or self.env,
                              capture_output=True, text=True, timeout=15)

    def fault(self, command, script):
        folder = self.root / 'bin'
        folder.mkdir(exist_ok=True)
        target = folder / command
        target.write_text('#!/bin/sh\n' + script)
        target.chmod(0o755)
        return self.env | {'PATH': f'{folder}:{self.env["PATH"]}'}

    def assert_pending_denies(self):
        self.assertTrue((self.state / '.pending').exists())
        self.assertNotEqual(self.run_cli('status', self.did).returncode, 0)
        self.assertNotEqual(self.run_cli('grant', self.did, '100', 'retry_blocked_01').returncode, 0)
        self.assertNotEqual(self.run_cli('init').returncode, 0)

    def test_replay_and_conflict_without_pending(self):
        tx = 'grant_20261109_01'
        first = self.run_cli('grant', self.did, '300', tx)
        again = self.run_cli('grant', self.did, '300', tx)
        wrong = self.run_cli('grant', self.did, '301', tx)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('replayed=true', again.stdout)
        self.assertNotEqual(wrong.returncode, 0)
        self.assertEqual((self.state / 'state.tsv').read_text().count('\nR\t'), 1)
        self.assertFalse((self.state / '.pending').exists())

    def test_concurrent_same_receipt_remains_single(self):
        tx = 'concurrent_20261109_1'
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs = [pool.submit(self.run_cli, 'grant', self.did, '100', tx) for _ in range(3)]
        outputs = [f.result() for f in jobs]
        self.assertTrue(all(r.returncode == 0 for r in outputs), outputs)
        self.assertEqual(sum('replayed=false' in r.stdout for r in outputs), 1)
        self.assertEqual((self.state / 'state.tsv').read_text().count('\nR\t'), 1)

    def test_intent_sync_failure_is_blocking(self):
        before = (self.state / 'state.tsv').read_bytes()
        env = self.fault('sync', 'exit 9\n')
        result = self.run_cli('grant', self.did, '90', 'intent_failure_01', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('lease_until=', result.stdout)
        self.assertEqual((self.state / 'state.tsv').read_bytes(), before)
        self.assert_pending_denies()

    def test_ledger_sync_failure_blocks_even_if_rename_done(self):
        counter = self.root / 'count'
        env = self.fault('sync', f'n=$(cat "{counter}" 2>/dev/null || echo 0)\nn=$((n+1))\necho "$n" > "{counter}"\n[ "$n" -ne 2 ] || exit 9\n/usr/bin/sync\n')
        result = self.run_cli('grant', self.did, '90', 'ledger_failure_01', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('lease_until=', result.stdout)
        self.assertIn('R\tledger_failure_01\t', (self.state / 'state.tsv').read_text())
        self.assert_pending_denies()

    def test_final_sync_failure_recreates_marker(self):
        counter = self.root / 'count'
        env = self.fault('sync', f'n=$(cat "{counter}" 2>/dev/null || echo 0)\nn=$((n+1))\necho "$n" > "{counter}"\n[ "$n" -ne 3 ] || exit 9\n/usr/bin/sync\n')
        result = self.run_cli('grant', self.did, '90', 'final_failure_01', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('lease_until=', result.stdout)
        self.assert_pending_denies()

    def test_atomic_rename_failure_preserves_previous_ledger(self):
        before = (self.state / 'state.tsv').read_bytes()
        env = self.fault('mv', 'exit 7\n')
        result = self.run_cli('grant', self.did, '90', 'rename_failure_01', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.state / 'state.tsv').read_bytes(), before)
        self.assert_pending_denies()

    def test_bad_reference_and_overflow_are_rejected(self):
        ledger = self.state / 'state.tsv'
        ledger.write_text(ledger.read_text() + f'R\tunknown_device_01\t{"f"*24}\t30\t1799999999\n')
        self.assertNotEqual(self.run_cli('grant', self.did, '90', 'badref_denied_01').returncode, 0)
        ledger.write_text(ledger.read_text().replace('unknown_device_01', 'valid_device_ref') .replace('f'*24, self.did) .replace('1799999999', '4999999999'))
        self.assertNotEqual(self.run_cli('status', self.did).returncode, 0)

    def test_invalid_grants_and_conflicting_receipts_do_not_mutate(self):
        before = (self.state / 'state.tsv').read_bytes()
        attempts = [
            ('grant', self.did, '0', 'bad_zero_123456'),
            ('grant', self.did, '3000000', 'bad_max_1234567'),
            ('grant', 'f'*24, '60', 'bad_device_123'),
            ('grant', self.did, '60', 'short'),
        ]
        for args in attempts:
            with self.subTest(args=args):
                self.assertNotEqual(self.run_cli(*args).returncode, 0)
                self.assertEqual((self.state / 'state.tsv').read_bytes(), before)
        self.assertEqual(self.run_cli('grant', self.did, '60', 'conflict_tx_123').returncode, 0)
        after = (self.state / 'state.tsv').read_bytes()
        self.assertNotEqual(self.run_cli('grant', self.did, '61', 'conflict_tx_123').returncode, 0)
        self.assertEqual((self.state / 'state.tsv').read_bytes(), after)

    def test_malformed_crypto_output_is_denied(self):
        before = (self.state / 'state.tsv').read_bytes()
        env = self.fault('openssl', 'echo "not-a-hex-key"\nexit 0\n')
        result = self.run_cli('register', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('device_secret=', result.stdout)
        self.assertEqual((self.state / 'state.tsv').read_bytes(), before)

    def test_unowned_lock_is_not_removed_on_timeout(self):
        lock = self.state / '.lock'
        lock.mkdir()
        try:
            result = self.run_cli('grant', self.did, '60', 'blocked_lock_123')
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(lock.is_dir())
        finally:
            lock.rmdir()

    def test_writer_killed_after_rename_leaves_uncertain_state(self):
        # Only kills the shell launched by the subprocess, never the test runner.
        counter = self.root / 'kill_count'
        env = self.fault('sync', f'n=$(cat "{counter}" 2>/dev/null || echo 0)\nn=$((n+1))\necho "$n" > "{counter}"\nif [ "$n" -eq 2 ]; then kill -KILL "$PPID"; exit 9; fi\n/usr/bin/sync\n')
        result = self.run_cli('grant', self.did, '90', 'kill_after_move_01', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('R\tkill_after_move_01\t', (self.state / 'state.tsv').read_text())
        self.assertTrue((self.state / '.lock').is_dir())
        self.assert_pending_denies()

    def test_busybox_shell_syntax(self):
        for filename in [CLI, LIB]:
            self.assertEqual(subprocess.run(['busybox','sh','-n',str(filename)], capture_output=True).returncode, 0)

    def test_http_status_denies_pending_after_rename(self):
        nonce = 'deadbeef00112233deadbeef00112233'
        sig = hmac.new(bytes.fromhex(self.identity['device_secret']),
                       f'v1|status|{self.did}|{nonce}'.encode(), hashlib.sha256).hexdigest()
        env = self.env | {'REQUEST_METHOD': 'GET', 'QUERY_STRING':
                          f'action=status&device_id={self.did}&nonce={nonce}&sig={sig}'}
        def http():
            cp = subprocess.run(['sh', str(CGI)], env=env,
                                capture_output=True, text=True, timeout=15)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            return json.loads(cp.stdout.partition('\n\n')[2])
        self.assertTrue(http()['ok'])
        (self.state / '.pending').write_text('PENDING\n')
        self.assertFalse(http()['ok'])

    def test_registration_does_not_emit_key_when_sync_fails(self):
        before = (self.state / 'state.tsv').read_bytes()
        env = self.fault('sync', 'exit 9\n')
        r = self.run_cli('register', env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('device_secret=', r.stdout)
        self.assertEqual((self.state / 'state.tsv').read_bytes(), before)
        self.assert_pending_denies()


if __name__ == '__main__':
    unittest.main()
