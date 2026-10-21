#!/usr/bin/env bash
# Open the dev build's Calc in one step, with a chosen look: office.sh for Calc.
# Usage: calc.sh [light|dark|tabbed|tabbed-light|compact] [--font system|selawik|inter] [--profile DIR] [--dry-run]
# The modes, options and default profile (/mnt/games/libreoffice/try-profile) are office.sh's.
OFFICE_USAGE=calc.sh exec "$(dirname "$0")/office.sh" calc "$@"
