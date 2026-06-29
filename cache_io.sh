#!/usr/bin/env bash
# cache_io.sh — Read and write report_cache.json via GitHub Contents API
# Auth is handled by the environment proxy — no REPORT_GITHUB_TOKEN needed.
# Usage:
#   source cache_io.sh
#   fetch_cache          → downloads report_cache.json to /tmp, prints content
#   push_cache <file>    → uploads the given JSON file to the repo

CACHE_REPO="mrmclaude1/Daily-Market-Intelligence-Report"
CACHE_FILE="report_cache.json"
CACHE_API="https://api.github.com/repos/${CACHE_REPO}/contents/${CACHE_FILE}"
CACHE_LOCAL="/tmp/report_cache.json"
CACHE_SHA_FILE="/tmp/report_cache_sha.txt"

fetch_cache() {
  local RESPONSE
  RESPONSE=$(curl -sS \
    -H "Accept: application/vnd.github.v3+json" \
    "${CACHE_API}" 2>&1)

  if echo "$RESPONSE" | grep -q '"message": "Not Found"'; then
    echo "BASELINE: Cache file not found — this is the first run." >&2
    echo "BASELINE"
    return 0
  fi

  echo "$RESPONSE" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
content = base64.b64decode(d['content']).decode('utf-8')
sha = d['sha']
with open('${CACHE_LOCAL}', 'w') as f:
    f.write(content)
with open('${CACHE_SHA_FILE}', 'w') as f:
    f.write(sha)
print('LOADED')
" 2>&1

  if [ $? -eq 0 ]; then
    echo "Cache loaded from GitHub ($(wc -c < ${CACHE_LOCAL}) bytes)" >&2
    cat "${CACHE_LOCAL}"
  else
    echo "ERROR: Failed to decode cache file." >&2
    echo "BASELINE"
    return 1
  fi
}

push_cache() {
  local INPUT_FILE="${1:-${CACHE_LOCAL}}"

  if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Cache file not found: $INPUT_FILE" >&2
    return 1
  fi

  local CONTENT
  CONTENT=$(base64 -w 0 < "$INPUT_FILE")

  local TODAY
  TODAY=$(date -u +"%Y-%m-%d")

  local PAYLOAD
  if [ -f "${CACHE_SHA_FILE}" ]; then
    local SHA
    SHA=$(cat "${CACHE_SHA_FILE}")
    PAYLOAD=$(python3 -c "
import json
print(json.dumps({'message': 'cache: ${TODAY}', 'content': '${CONTENT}', 'sha': '${SHA}'}))
")
  else
    PAYLOAD=$(python3 -c "
import json
print(json.dumps({'message': 'cache: ${TODAY}', 'content': '${CONTENT}'}))
")
  fi

  local RESPONSE
  RESPONSE=$(curl -sS -X PUT \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "${CACHE_API}" 2>&1)

  if echo "$RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
sha=d.get('content',{}).get('sha','')
if sha:
    with open('${CACHE_SHA_FILE}','w') as f: f.write(sha)
    print('SHA updated:', sha[:8])
else:
    sys.exit(1)
" 2>/dev/null; then
    echo "✅ Cache pushed for ${TODAY}" >&2
    return 0
  else
    echo "❌ Push failed:" >&2
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE" >&2
    return 1
  fi
}
