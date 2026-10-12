#!/usr/bin/env bash
# Run gbuild in the LibreOffice core checkout under a memory cap.
# A full -j10 build froze the 14 GB dev machine on 2026-10-12; confining make
# to a cgroup scope keeps the desktop responsive (peak observed: 4.8 GB at -j6).
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
exec systemd-run --user --scope --quiet \
    -p MemoryHigh=6G -p MemoryMax=7G -p MemorySwapMax=1G \
    nice -n 10 make -C "$core" PARALLELISM="${PARALLELISM:-6}" "$@"
