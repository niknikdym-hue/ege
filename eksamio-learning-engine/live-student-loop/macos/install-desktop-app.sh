#!/bin/bash
set -euo pipefail
[[ "$(uname)" == Darwin ]] || { echo 'macOS required' >&2; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"; RUNTIME="$(cd "$HERE/.." && pwd)/runtime.py"
PYTHON="${EKSAMIO_PYTHON:-$(command -v python3)}"; "$PYTHON" -c "import jsonschema; import sys; sys.path.insert(0,'$(dirname "$RUNTIME")'); import runtime"
APP="$HOME/Desktop/Eksamio — Ученик STAGING.app"; TMP="${APP}.tmp"; rm -rf "$TMP"; mkdir -p "$TMP/Contents/MacOS"
xcrun swiftc -O -framework AppKit -framework Foundation -framework Security "$HERE/EksamioStudentStaging.swift" -o "$TMP/Contents/MacOS/EksamioStudentStaging"
cat > "$TMP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>CFBundleExecutable</key><string>EksamioStudentStaging</string><key>CFBundleIdentifier</key><string>ru.eksamio.student-staging</string><key>EksamioPython</key><string>$PYTHON</string><key>EksamioRuntime</key><string>$RUNTIME</string></dict></plist>
EOF
rm -rf "$APP"; mv "$TMP" "$APP"; echo "$APP"
