#!/bin/sh
# Refresh the DocEngine's vendored engine from the repository's pp-document-suite.
# Since the canon revision of 09.10.2026 the suite is the single source; this copy exists
# only because the DocEngine image is built from apps/wwf-docengine. tests/test_engine_sync.py
# fails CI when the two differ, so run this after every change to pp-document-suite.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
SUITE=$(cd "$HERE/../../../pp-document-suite" && pwd)
rm -rf "$HERE/scripts" "$HERE/assets" "$HERE/references"
mkdir -p "$HERE/scripts"
cp "$SUITE"/scripts/*.py "$SUITE"/scripts/*.sh "$SUITE"/scripts/*.ps1 "$HERE/scripts/"
cp -r "$SUITE/assets" "$HERE/assets"
cp -r "$SUITE/references" "$HERE/references"
echo "engine synced from $SUITE"
