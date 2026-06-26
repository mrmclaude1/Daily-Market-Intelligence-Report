#!/usr/bin/env bash
# cache_io.sh — Read and write report_cache.json via GitHub Contents API
# Usage:
#   source cache_io.sh
#   fetch_cache          → downloads report_cache.json, prints its content
#   push_cache <file>    → uploads the given JSON file to the repo

CACHE_REPO="mrmclaude1/Daily-Market-Intelligence-Report"
CACHE_FILE="report_cache.json"
CACHE_API="https://api.github.com/repos/${CACHE_REPO}/contents/${CACHE_FILE}"
CACHE_LOCAL="/tmp/report_cache.json"
CACHE_SHA_FILE="/tmp/report_cache_sha.txt"

fetch_cache() {
  local TOKEN="${REPORT_GITHUB_TOKEN}"
  if [ -z "$TOKEN" ]; then
    echo "ERROR: REPORT_GITHUB_TOKEN not set. Cannot fetch previous report cache." >&2
    echo "BASELINE"
    return 1
  fi

  local RESPONSE
  RESPONSE=$(curl -sS \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "${CACHE_API}" 2>&1)

  local HTTP_STATUS
  HTTP_STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK')" 2>/dev/null && echo "OK" || echo "ERR")

  if echo "$RESPONSE" | grep -q '"message": "Not Found"'; then
    echo "BASELINE: Cache file not found in repo — this is the first run." >&2
    echo "BASELINE"
    return 0
  fi

  # Extract and decode base64 content
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
  local TOKEN="${REPORT_GITHUB_TOKEN}"

  if [ -z "$TOKEN" ]; then
    echo "ERROR: REPORT_GITHUB_TOKEN not set. Cannot push cache." >&2
    return 1
  fi

  if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Cache file not found: $INPUT_FILE" >&2
    return 1
  fi

  # Base64-encode the content
  local CONTENT
  CONTENT=$(base64 -w 0 < "$INPUT_FILE")

  local TODAY
  TODAY=$(date -u +"%Y-%m-%d")

  # Build JSON payload — include SHA if updating existing file
  local PAYLOAD
  if [ -f "${CACHE_SHA_FILE}" ]; then
    local SHA
    SHA=$(cat "${CACHE_SHA_FILE}")
    PAYLOAD=$(python3 -c "
import json
payload = {
  'message': 'Report cache update ${TODAY}',
  'content': '${CONTENT}',
  'sha': '${SHA}'
}
print(json.dumps(payload))
")
  else
    PAYLOAD=$(python3 -c "
import json
payload = {
  'message': 'Report cache init ${TODAY}',
  'content': '${CONTENT}'
}
print(json.dumps(payload))
")
  fi

  local RESPONSE
  RESPONSE=$(curl -sS -X PUT \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "${CACHE_API}" 2>&1)

  if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content',{}).get('sha',''))" 2>/dev/null | grep -q .; then
    echo "Cache successfully pushed to GitHub for ${TODAY}" >&2
    # Update local SHA for next push within the same run
    echo "$RESPONSE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
sha = d.get('content',{}).get('sha','')
if sha:
    with open('${CACHE_SHA_FILE}','w') as f: f.write(sha)
    print('SHA updated: ' + sha[:8])
" 2>/dev/null
    return 0
  else
    echo "ERROR pushing cache to GitHub:" >&2
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE" >&2
    return 1
  fi
}
