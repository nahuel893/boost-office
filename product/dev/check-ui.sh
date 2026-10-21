#!/usr/bin/env bash
# Run the build's accessibility check (bin/gla11y) and bin/lint-ui.py on app .ui files.
# Each <dir>/uiconfig/<module>/ui/*.ui file is checked against its module's sanitizer files,
# solenv/sanitizers/ui/modules/<module>.false and .suppr, as the build does.
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$core"
report="$(mktemp)"
trap 'rm -f "$report"' EXIT
status=0
for ui in "$@"; do
    case "$ui" in
        */uiconfig/*/ui/*.ui) module="${ui#*/uiconfig/}"; module="${module%%/*}" ;;
        *) echo "check-ui.sh: $ui is not an app .ui file (<dir>/uiconfig/<module>/ui/*.ui)" >&2; exit 2 ;;
    esac
    : >"$report"   # a run that fails before writing must not reprint the previous file's report
    python3 -I bin/gla11y -P ./ -f "solenv/sanitizers/ui/modules/$module.false" \
        -s "solenv/sanitizers/ui/modules/$module.suppr" \
        --widgets-suffixignored +ValueSet,HBox,VBox,ToolBox,Preview,PreviewWin,PreviewWindow,PrevWindow \
        --widgets-button +svtlo-ManagedMenuButton \
        --fatal-all --not-fatal-type duplicate-mnemonic --not-fatal-type labelled-by-and-mnemonic \
        --not-fatal-type orphan-label -o "$report" "$ui" || status=1
    printf '%s\n' "$(<"$report")"
done
python3 -I bin/lint-ui.py "$@" || status=1
exit $status
