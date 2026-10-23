#!/usr/bin/env bash
# Run UITests one by one. Names must be full: module.Class.test
# (uitest/test_main.py only filters on an exact full name).
# Usage: uitest.sh [--app calc|writer|impress] NAME...
#   --app  calc (default): UITest_calc_tests; writer: UITest_writer_tests8; impress: UITest_impress_tests2
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
core="$(cd "$here/../.." && pwd)"
usage() { echo "usage: uitest.sh [--app calc|writer|impress] module.Class.test..." >&2; exit 2; }
app=calc
if [ "${1:-}" = --app ]; then
    [ $# -ge 2 ] || usage
    app="$2"; shift 2
fi
case "$app" in
    calc) target=calc_tests ;;
    writer) target=writer_tests8 ;;
    impress) target=impress_tests2 ;;
    *) usage ;;
esac
status=0
for name in "$@"; do
    echo "== $name"
    if ! "$here/lo-make.sh" "UITest_$target" UITEST_TEST_NAME="$name"; then
        status=1
        tail -n 40 "$core/workdir/UITest/$target/done.log" 2>/dev/null || true
    fi
done
exit $status
