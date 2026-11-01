#!/usr/bin/env bash
# Build the two Claude Desktop extensions (.mcpb) into dist/.
#   garmin-coach-<version>.mcpb                  all-in-one, read-only (official Garmin Personal API)
#   garmin-coach-docker-connector-<version>.mcpb connects Claude Desktop to a Docker server
# Requirements: uv, Node.js/npm.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MCPB="npx -y @anthropic-ai/mcpb@2.1.2"
VERSION="$(python3 -c 'import json;print(json.load(open("packaging/extension/manifest.json"))["version"])')"

rm -rf build dist
mkdir -p build dist

# --- all-in-one extension (Python, run by Claude Desktop through uv)
EXT=build/extension
cp -r packaging/extension "$EXT"
cp -r app "$EXT/src/app"
find "$EXT" -name __pycache__ -prune -exec rm -rf {} +
cp LICENSE THIRD_PARTY_NOTICES.md "$EXT/"
(cd "$EXT" && uv lock --quiet)
$MCPB validate "$EXT/manifest.json"
$MCPB pack "$EXT" "dist/garmin-coach-$VERSION.mcpb"

# --- Docker connector (Node, mcp-remote bundled)
CON=build/connector
cp -r packaging/connector "$CON"
cp LICENSE THIRD_PARTY_NOTICES.md "$CON/"
(cd "$CON" && npm install --omit=dev --no-audit --no-fund --silent)
$MCPB validate "$CON/manifest.json"
$MCPB pack "$CON" "dist/garmin-coach-docker-connector-$VERSION.mcpb"

ls -lh dist
