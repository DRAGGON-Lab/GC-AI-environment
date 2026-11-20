#!/usr/bin/env bash
# Check that a running GC-AI stack answers on all three services.
set -euo pipefail

FRONTEND_PORT="${FRONTEND_PORT:-8081}"
BACKEND_PORT="${BACKEND_PORT:-5001}"
BACKEND="http://localhost:${BACKEND_PORT}"
FRONTEND="http://localhost:${FRONTEND_PORT}"

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

# A part lookup is the check that the API is usable: it only succeeds when the
# application is serving, the detection model has loaded, and the parts database
# answers queries. The /healthcheck/ endpoint always reports 500 in this build,
# so it is not a usable signal.
echo "1/3 backend and parts database (${BACKEND}/component/names?role=Promoter)"
names=$(curl -fsS --max-time 60 "${BACKEND}/component/names?role=Promoter") ||
	fail "could not list promoter names; try 'docker compose logs backend db'"
count=$(printf '%s' "${names}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))') ||
	fail "promoter names were not valid JSON: ${names}"
[ "${count}" -gt 0 ] || fail "the parts table returned no promoters, so the database is empty"
echo "    ok: ${count} promoter names"

echo "2/3 part details (${BACKEND}/component/details?component_name=BBa_R0010)"
detail=$(curl -fsS --max-time 60 "${BACKEND}/component/details?component_name=BBa_R0010&role=Promoter") ||
	fail "could not read BBa_R0010; try 'docker compose logs backend db'"
printf '%s' "${detail}" | python3 -c '
import json, sys
part = json.load(sys.stdin)
if not part.get("sequence"):
    sys.exit("BBa_R0010 came back without a sequence")
print("    ok: BBa_R0010, %d nt" % len(part["sequence"]))
' || fail "part details were not usable: ${detail}"

echo "3/3 web interface (${FRONTEND})"
curl -fsS --max-time 30 -o /dev/null "${FRONTEND}" ||
	fail "frontend did not respond; try 'docker compose logs frontend'"
echo "    ok"

echo "GC-AI is up: ${FRONTEND}"
