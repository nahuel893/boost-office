#!/usr/bin/env bash
# Run Calc UITests one by one. Names must be full: module.Class.test
# (uitest/test_main.py only filters on an exact full name).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
core="$(cd "$here/../.." && pwd)"
status=0
for name in "$@"; do
    echo "== $name"
    if ! "$here/lo-make.sh" UITest_calc_tests UITEST_TEST_NAME="$name"; then
        status=1
        tail -n 40 "$core/workdir/UITest/calc_tests/done.log" 2>/dev/null || true
    fi
done
exit $status
