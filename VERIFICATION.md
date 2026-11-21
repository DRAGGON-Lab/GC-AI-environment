# Deployment verification record

Implementation baseline: `059eff4e5b1906184fe2eee29089693c66e65597` of
`cvtalrc/GC-AI-environment`. This record covers the uncommitted implementation
on 2026-11-21; review the final PR revision before execution.

Local environment: macOS, Python 3.7.3 for environment scripts, Docker Compose
v5.3.0. Commands executed from this repository:

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | Exit 0; 7 passed, including independently rendered local and hosted Compose configuration, plus mocked legacy-import filesystem and cleanup paths |
| `python3 -m py_compile scripts/import-assets.py scripts/prepare-secrets.py` | Exit 0 |
| `bash -n scripts/10-import-registry.sh scripts/20-create-app-user.sh tests/docker-smoke.sh` | Exit 0 |
| `sh -n scripts/backup.sh scripts/root-sql.sh` | Exit 0 |
| `git diff --check` | Exit 0 |
| `docker info --format '{{.ServerVersion}}'` | Exit 1; Docker socket missing |

Rendered configuration tests supply synthetic image digests only to validate
configuration; they do not claim those images exist. Private input values are
not recorded. `tests/docker-smoke.sh` and the manual Docker workflow have **not
run locally**. The workflow takes an exact reviewed GC-AI commit SHA; its
checkpoint fixture intentionally establishes only degraded readiness. It does
not establish real checkpoint/GPU execution, legacy asset migration, deployed
credential rotation, or production readiness.

Required operator evidence remains: source revision and actual image digests,
trusted checkpoint provenance and execution, legacy import receipt with asset
hashes, hosted authentication and inference smoke results, least-privilege grants,
backup/restore outcome, janitor outcome, and actual credential-rotation receipt.
Keep the deployment child and Epic #7 open until those are accepted.

Follow-up importer regression reproduced failure for both successful-dump and
failed-dump paths before the fix. The regression verifies the ephemeral file is
0444 under a 0700 host parent while the original client file stays 0600, root
client exec is explicit, containers and temporary credentials are removed on
success/failure, and credential values never enter Docker command arguments.
These are mocked Docker executions; real legacy-image import remains not_run.
