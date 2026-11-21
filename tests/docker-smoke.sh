#!/bin/bash
# CI-only fresh isolated project; never point this script at production volumes.
set -euo pipefail
source_dir=${1:?Usage: tests/docker-smoke.sh reviewed-source-directory}
if [[ ! "${GCAI_SOURCE_REF:-}" =~ ^[a-f0-9]{40}$ ]]; then
    echo 'GCAI_SOURCE_REF must be the reviewed full commit SHA' >&2; exit 1
fi
[[ $(git -C "$source_dir" rev-parse HEAD) == "$GCAI_SOURCE_REF" ]]
export COMPOSE_PROJECT_NAME="gcai-smoke-${GITHUB_RUN_ID:-$$}"
cleanup() { docker compose -f compose.hosted.yml down -v --remove-orphans; }
trap cleanup EXIT
mkdir -m 700 secrets assets receipts
export GCAI_UID=$(id -u) GCAI_GID=$(id -g)
export GCAI_TRUSTED_ORIGINS=https://localhost
python3 - <<'PY'
from pathlib import Path
import secrets, subprocess
for name in ('db_root_password','db_app_password'):
    path=Path('secrets')/name
    path.write_text(secrets.token_hex(32)); path.chmod(0o600)
password=secrets.token_hex(24)
hashed=subprocess.run(['openssl','passwd','-6','-stdin'],input=password,text=True,capture_output=True,check=True).stdout.strip()
Path('secrets/htpasswd').write_text('gcai:'+hashed+'\n')
Path('secrets/curl.conf').write_text('user = "gcai:'+password+'"\ncacert = "secrets/tls.crt"\n')
Path('secrets/htpasswd').chmod(0o600); Path('secrets/curl.conf').chmod(0o600)
Path('assets/160_model.pth').write_text('CI placeholder: real checkpoint/GPU smoke not_run')
Path('assets/160_model.pth').chmod(0o600)
Path('assets/registry.sql').write_text('CREATE TABLE parts (part_name VARCHAR(255) PRIMARY KEY, part_type VARCHAR(100), sequence TEXT); INSERT INTO parts VALUES ("ci-part","coding","atgc");\n')
Path('assets/registry.sql').chmod(0o600)
PY
openssl req -x509 -newkey rsa:2048 -nodes -keyout secrets/tls.key -out secrets/tls.crt -days 1 -subj /CN=localhost -addext subjectAltName=DNS:localhost >/dev/null 2>&1
chmod 600 secrets/tls.*
docker build -f "$source_dir/backend/Dockerfile" -t gcai-backend-smoke "$source_dir"
docker build -f "$source_dir/frontend/Dockerfile" -t gcai-frontend-smoke "$source_dir"
docker pull mysql:8.4
export GCAI_BACKEND_IMAGE=$(docker image inspect gcai-backend-smoke --format '{{.Id}}')
export GCAI_FRONTEND_IMAGE=$(docker image inspect gcai-frontend-smoke --format '{{.Id}}')
export GCAI_MYSQL_IMAGE=$(docker image inspect mysql:8.4 --format '{{index .RepoDigests 0}}')
export GCAI_MYSQL_UID=$(docker run --rm --network none --entrypoint id "$GCAI_MYSQL_IMAGE" -u mysql)
export GCAI_MYSQL_GID=$(docker run --rm --network none --entrypoint id "$GCAI_MYSQL_IMAGE" -g mysql)
export GCAI_NGINX_UID=$(docker run --rm --network none --entrypoint id "$GCAI_FRONTEND_IMAGE" -u nginx)
export GCAI_NGINX_GID=$(docker run --rm --network none --entrypoint id "$GCAI_FRONTEND_IMAGE" -g nginx)
docker compose -f compose.hosted.yml config --quiet
docker compose -f compose.hosted.yml up -d
for attempt in $(seq 1 90); do
    if curl --config secrets/curl.conf -fsS https://localhost/api/livez >/dev/null 2>&1; then break; fi
    sleep 2
done
[[ $(curl --cacert secrets/tls.crt -sS -o /dev/null -w '%{http_code}' https://localhost/) == 401 ]]
[[ $(curl --cacert secrets/tls.crt -sS -o /dev/null -w '%{http_code}' https://localhost/api/livez) == 401 ]]
curl --config secrets/curl.conf -fsS https://localhost/api/livez >/dev/null
curl --config secrets/curl.conf -fsS https://localhost/ | python3 -c 'import sys; assert "<!doctype html>" in sys.stdin.read().lower()'
[[ $(curl --config secrets/curl.conf -sS -o /dev/null -w '%{http_code}' https://localhost/api/healthcheck/) == 503 ]]
[[ $(curl --config secrets/curl.conf -sS -X POST -H 'Origin: https://untrusted.invalid' -o /dev/null -w '%{http_code}' https://localhost/api/inference/) == 403 ]]
# Fresh data and application SELECT work; INSERT must fail with restricted grants.
docker compose -f compose.hosted.yml exec -T db sh -c '
 set -eu; umask 077; config=$(mktemp); trap '\''rm -f "$config"'\'' EXIT
 printf "[client]\nuser=gcai\npassword=%s\n" "$(cat /run/gcai/db_app_password)" > "$config"
 test "$(mysql --defaults-extra-file="$config" --batch --skip-column-names iGEM2024 -e "SELECT COUNT(*) FROM parts")" = 1
 if mysql --defaults-extra-file="$config" iGEM2024 -e "INSERT INTO parts VALUES (\"forbidden\",\"coding\",\"a\")" 2>/dev/null; then exit 1; fi
 mysql --defaults-extra-file="$config" -e "SHOW GRANTS" | tail -n +2
' > receipts/application-grants.txt
printf "SELECT User,Host FROM mysql.user WHERE User='root' AND Host<>'localhost';\n" > receipts/check-root.sql
scripts/root-sql.sh receipts/check-root.sql > receipts/remote-root.txt
test ! -s receipts/remote-root.txt
scripts/backup.sh receipts/registry-backup.sql
scripts/root-sql.sh receipts/registry-backup.sql
# Expired immutable metadata is removed through the production cleanup command.
docker compose -f compose.hosted.yml run --rm -T --no-deps --entrypoint python janitor - <<'PY'
import os,time,json
from pathlib import Path
from app.utils.artifacts import ArtifactStore
store=ArtifactStore(os.environ['GCAI_ARTIFACT_DIR'])
handle=store.publish(b'<x/>', b'<x/>', now=time.time()-86401)
import subprocess
subprocess.run(['python','-m','app.utils.cleanup'],check=True)
assert not (Path(store.root)/handle).exists()
print('Production cleanup command removed expired artifact')
PY
# Run actual route and archive semantics using source tests inside the image.
docker compose -f compose.hosted.yml run --rm -T --no-deps --entrypoint python \
 -v "$(cd "$source_dir" && pwd):/source:ro" \
 backend -m pytest /source/backend/tests/test_namespaces.py /source/backend/tests/test_artifacts.py /source/backend/tests/test_conversion_handles.py -q --disable-warnings
python3 - <<'PY'
import json,os,time
from pathlib import Path
Path('receipts/ci-execution.json').write_text(json.dumps({
 'source_revision':os.environ['GCAI_SOURCE_REF'],
 'backend_image_id':os.environ['GCAI_BACKEND_IMAGE'],
 'frontend_image_id':os.environ['GCAI_FRONTEND_IMAGE'],
 'mysql_image_digest':os.environ['GCAI_MYSQL_IMAGE'],
 'executed_at_unix':time.time(),'real_checkpoint_gpu':'not_run: deliberate CI placeholder',
 'production_migration':'not_run','credential_rotation':'not_run'},indent=2)+'\n')
PY
