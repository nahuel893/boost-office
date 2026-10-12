#!/usr/bin/env bash
# Run the build's accessibility check (bin/gla11y) and bin/lint-ui.py on Calc .ui files.
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$core"
report="$(mktemp)"
trap 'rm -f "$report"' EXIT
status=0
python3 -I bin/gla11y -P ./ -f solenv/sanitizers/ui/modules/scalc.false \
    -s solenv/sanitizers/ui/modules/scalc.suppr \
    --widgets-suffixignored +ValueSet,HBox,VBox,ToolBox,Preview,PreviewWin,PreviewWindow,PrevWindow \
    --widgets-button +svtlo-ManagedMenuButton \
    --fatal-all --not-fatal-type duplicate-mnemonic --not-fatal-type labelled-by-and-mnemonic \
    --not-fatal-type orphan-label -o "$report" "$@" || status=1
printf '%s\n' "$(<"$report")"
python3 -I bin/lint-ui.py "$@" || status=1
exit $status
