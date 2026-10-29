#!/usr/bin/env bash
# Quick "does the deployed app really answer?" check using curl.
# Usage: ci/smoke_test.sh <container-name> <port>
set -eu                                  # stop at the first problem

NAME="$1"                                # container to test, reachable by name on the shared Docker network
PORT="$2"                                # its port

# The app only answers requests addressed to "localhost:<port>", so we send that name in the Host header.
BASE="http://$NAME:$PORT"
HOST_HEADER="Host: localhost:$PORT"

# 1. Home page must answer 200 and be HTML.
curl -fsS -H "$HOST_HEADER" "$BASE/" | grep -qi "<html"
echo "OK: home page"

# 2. The demo data must be served and say it is demo data.
curl -fsS -H "$HOST_HEADER" "$BASE/demo_data.json" | grep -q '"demo":true'
echo "OK: demo data"

# 3. A private file must NOT be reachable (security check).
code="$(curl -s -o /dev/null -w '%{http_code}' -H "$HOST_HEADER" "$BASE/google_tokens.json")"
[ "$code" = "404" ]
echo "OK: private files are hidden (got $code)"

echo "SMOKE TEST PASSED for $NAME"
