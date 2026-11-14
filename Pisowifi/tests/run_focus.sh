#!/bin/sh
# Disposable shell tests: these mock nft/UCI and MUST NOT access a live router.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for test_file in \
  capabilities.sh \
  controller_registration_defaults.sh \
  controller_registry_write_fault.sh \
  nft_atomic_setup.sh \
  nft_shutdown_guard.sh \
  nft_membership_failclosed.sh \
  nft_account_binding_guard.sh \
  config_faults.sh \
  config_apply_failclosed.sh \
  config_concurrency.sh \
  admin_config_result.sh \
  config_fixture_smoke.sh \
  bootstrap_and_cli_auth_guard.sh \
  portal.sh \
  security.sh \
  config.sh \
  member_receipt_failure_atomicity.sh \
  member_txn_journal.sh \
  voucher_txn_journal.sh \
  integration.sh
do
  printf 'RUN %s\n' "$test_file"
  sh "$ROOT/tests/$test_file"
done
printf 'ALL FOCUSED SHELL TESTS PASS (MOCKS ONLY)\n'
