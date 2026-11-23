# Deployment verification record

Implementation baseline: `059eff4e5b1906184fe2eee29089693c66e65597` of
`cvtalrc/GC-AI-environment`. This record covers the uncommitted implementation
on 2026-11-21; review the final PR revision before execution.

Local environment: macOS, Python 3.7.3 for environment scripts, Docker Compose
v5.3.0. Commands executed from this repository:

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | Exit 0; 8 passed, including independently rendered local and hosted Compose configuration, plus mocked legacy-import filesystem and cleanup paths |
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

The Docker smoke now also exercises healthy readiness in an isolated backend
Python process with only `config.model` replaced by an object. Its actual Flask
health route uses the real MySQL connector, mounted application secret, private
network and consumed `SELECT 1`. This does not mutate the Gunicorn worker or
claim checkpoint/GPU initialization. The smoke then sends authenticated TLS
create/convert requests through Nginx and Gunicorn, retaining the handle only in
private files. Both requested ZIP entries are parsed with BioPython inside the
backend, with exact sequence identities/bases and GenBank feature coordinates
asserted. These new checks have syntax/static verification only until the
Docker workflow executes; no new runtime pass is claimed by this record.

## Confirmed MySQL TCP health-probe correction (2026-11-23)

The Docker MySQL-only run produced sanitized diagnostics showing successful
registry/database initialization followed by health-probe error 1045 for
`root@127.0.0.1`. The deliberate `MYSQL_ROOT_HOST=localhost` restriction does not
permit that TCP identity. The health probe now uses the existing SELECT-only
`gcai` account and its mounted application password for TCP `SELECT 1`; root
remains restricted to localhost. TCP is retained to avoid reporting the
entrypoint's temporary socket-only initialization server as healthy.

The updated regression first failed against the root-password probe, then
passed after the correction. It executes the rendered shell with a fake MySQL
client that parses the actual temporary 0600 INI, requires application-user
credentials and TCP `SELECT 1`, and verifies temporary-file cleanup. Substituting
root back into the command fails the same regression. All eight static tests,
Python compilation, shell syntax, and diff whitespace checks pass. Actual
post-fix MySQL and full deployment Docker reruns remain pending; no successful
runtime result is inferred from these static checks.
