#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_SPEC="$ROOT_DIR/deploy/openapi.json"
UPLOAD_SPEC="$ROOT_DIR/open.json"

if [[ ! -f "$SOURCE_SPEC" ]]; then
  echo "Error: source spec not found at $SOURCE_SPEC" >&2
  exit 1
fi

# Validate JSON before publishing upload artifact.
python3 - <<'PY' "$SOURCE_SPEC"
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

if "paths" not in data or not isinstance(data["paths"], dict):
    raise SystemExit("Invalid OpenAPI spec: missing 'paths' object")

print(f"Validated spec with {len(data['paths'])} paths")
PY

cp "$SOURCE_SPEC" "$UPLOAD_SPEC"

echo "Created upload-ready spec: $UPLOAD_SPEC"
