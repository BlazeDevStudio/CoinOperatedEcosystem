#!/bin/sh
# Disposable shell tests: these mock nft/UCI and MUST NOT access a live router.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for test_file in \
  capabilities.sh \
  nft_atomic_setup.sh \
  nft_shutdown_guard.sh \
  nft_membership_failclosed.sh \
  nft_account_binding_guard.sh \
  config_faults.sh
do
  printf 'RUN %s\n' "$test_file"
  sh "$ROOT/tests/$test_file"
done
printf 'ALL FOCUSED SHELL TESTS PASS (MOCKS ONLY)\n'
