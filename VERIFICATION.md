# Deployment verification evidence

Baseline: `059eff4e5b1906184fe2eee29089693c66e65597` of `DRAGGON-Lab/GC-AI-environment`. Source/configuration and Docker checks were executed on 2026-11-21 and 2026-11-23. This is synthetic CI evidence, not an operator migration or credential-rotation receipt.

Local checks on macOS: nine `unittest` configuration/security regressions pass, including rendered local/hosted networks, consumer-owned private secret copies, restricted MySQL health credentials, and complete legacy initialization before export. Python compilation, shell syntax and `git diff --check` pass. Local Docker remains unavailable (missing daemon socket); actual containers ran on GitHub's Docker-capable runners.

| Executed check | Result / evidence |
| --- | --- |
| Fresh MySQL initialization and grants | [Passed](https://github.com/Gonza10V/GC-AI-environment/actions/runs/45165181038): registry import, consumed SELECT1, application SELECT, rejected INSERT, no remote root accounts |
| Digest-pinned synthetic legacy import | Same passing workflow: stopped fake-byte checkpoint image, delayed SQL initialization in isolated MySQL, exact exported bytes/data and checksums, no accounts/grants/secrets in dump, cleanup of containers/anonymous volumes/staging |
| Proxy/network/authentication | Same passing workflow: actual published TLS443, unauthenticated401 with challenge, authenticated frontend/API200, request-size413, sanitized upstream503. Only the proxy joins the normal edge network; backend/database stay internal with no host ports. Uses a clearly identified stdlib backend stub |
| Full production-image hosted integration | [Passed](https://github.com/Gonza10V/GC-AI-environment/actions/runs/45171695936), application `fcde1215abf2460ff5cddf6d9d5ce6588b774f19`, environment `32abcc6a92530d1cbe3202a42cd00c74203ac855`: built reviewed application images, authenticated wire create/convert with exact formats/sequences/coordinates, rejected unsafe Origin, real MySQL connector/readiness with mocked detector, backup/restore and production janitor command |

The sanitized receipt and exact image identities are committed under [verification/hosted-smoke.json](verification/hosted-smoke.json); [application grants](verification/application-grants.txt) show only USAGE and SELECT on `iGEM2024.parts`. Source/image identities describe the executed CI snapshot. Subsequent documentation-only receipt updates do not change its tested runtime configuration.

Actual failures found and corrected before acceptance: MySQL/Nginx consumer secret readability; MySQL init scripts needing source scope; root account restriction; root-over-TCP health authentication; temporary MySQL initialization being mistaken for completed import; and Docker requiring a non-internal gateway network to publish proxy ports. Follow-up tests cover these boundaries rather than treating rendered configuration as proof of runtime success.

The checkpoint fixtures are deliberately synthetic. CI does not establish real checkpoint deserialization/detector output, GPU execution, real legacy-registry migration, production readiness, deployed credential rotation, browser conversion with the real detector, or operator acceptance. The recorded final image run includes the JPEG EXIF compatibility correction and bounded frontend registry loading. Application checks also passed: 177 backend tests, 146 client tests, 19 frontend tests, and strict dual-validator SBOL reconciliation.

Required operator receipt: approved source revisions and actual published image digests, checkpoint/registry provenance and import hashes, live authenticated inference/readiness/create/convert, frontend retry, least-privilege grants, backup/restore result, janitor result, denied old credentials after real rotation, and rollback location. Record no secret values. Keep issue #16 and Epic #7 open until the environment PR and these gates are accepted.


## DRAGGON-Lab review port — 24 November 2026

New baseline: DRAGGON-Lab/GC-AI-environment `2646936`. Hardened files were ported
from the coordinated implementation, preserving explicit linux/amd64 and legacy
image digests. Added localhost-only authenticated TLS review and private credential
initialization. Current-tree configuration and bootstrap checks are recorded
separately from the historical Docker receipts above. Actual current-tree image
build, hosted smoke, checkpoint execution and production rotation remain not_run.


Real asset discovery on 24 November 2026: the backend checkpoint was extracted
from its verified OCI layer without application execution, with the parent
manifest and all subsequent overlay layers verified. Checkpoint SHA256 is
`06ac3f64292ed93f49e296b60e32dab0b5b0182e86141b52ff43a253dba51749`
(518726586 bytes). An isolated no-network legacy database exported **84285**
parts; registry dump SHA256 is
`e869efcaa5bc37bc68065bb90eb48136d7319c1d52aec5a20dcdf4f045aa1766`.
Sanitized receipts are in verification; actual model/SQL files remain private and
ignored. The real image first failed initialization with `No database selected`;
adding `MYSQL_DATABASE=iGEM2024` fixed the export. Its regression failed before
the correction and all eleven configuration/bootstrap checks then passed.
This is local review asset extraction, not a production migration receipt.


Five live SBOL DB tests passed against pinned official image
`ghcr.io/marpaia/sbol-db@sha256:ec35a160248e1db1b50e2a55c251e140c6f2f6c0d5781822b5140aa475af759b`:
three regenerated-fixture publications with zero findings and RDF readback, SBOL2
conversion and overwrite. One GC-AI-to-registry test was skipped without a full
GC-AI service. Actual real-checkpoint CPU replay then matched boxes/classes for
all three committed inputs using Torch 2.6.0+cpu/TorchVision 0.21.0+cpu/Python 3.12.16;
see verification/checkpoint-replay.json. The isolated verifier had no network,
non-root execution, read-only inputs and resource limits. GPU execution is not
claimed. The disposable SBOL DB container/image/temporary volume were removed.

The current source tree's twelve configuration/bootstrap/import regressions pass.
The CPU verifier's real checkpoint replay passed all three historical detection
records exactly. Full authenticated local review stack startup is being checked
separately; this does not establish production cutover or GPU execution.


Actual local review bootstrap also exposed Docker Desktop reporting host-bound
init scripts as executable despite host0644. MySQL attempted execution instead
of sourcing and initialized no parts/application account. Scripts are now copied
as 0400 into a private mysql-owned named init volume before database startup.
The regression first failed, then all thirteen configuration/bootstrap checks
passed. The failed review project's volumes were preserved; the retry uses a
fresh project. This supersedes assumptions based only on host script permissions.


Full local TLS runtime gate passed all nine checks after real local-review
credential rotation: new root/application passwords authenticated, previous ones
were denied, and the previous workspace password received401. The real checkpoint
and 84285-part registry were used, not mocks. Private logical backup restored into
a fresh no-network MySQL 8.4 container with exactly 84285 rows and table checksum
2942824569 matching source; no application account was restored. Temporary restore
container/volume were removed. Production janitor removed an expired test artifact.
The full live client suite subsequently passed 22 tests (146 unit cases deselected),
and the complete real notebook executed with named parts, conversion, temporary
SBOL DB publication and cleanup. The notebook and inference suite were run
sequentially after an initial overlapping run correctly encountered503 admission.
These receipts describe local CPU review; production migration/rotation and GPU
execution remain unclaimed.

Final Chromium159 browser flow passed with the rebuilt frontend: all fourteen real
registry lists, real inference upload, required namespace, XML attachment filename,
and parsed FASTA/GenBank outputs. One browser-local synthetic503 exercised retry;
no partial download occurred and both selections/the same handle were retained.
See verification/local-review-browser.json. Runtime npm audit is zero; the two
remaining development-only Vite/esbuild advisories are documented by the app.

The optional one-GPU overlay and GPU-required acceptance regression are now
implemented. All14 environment checks pass; the application has10 independent
cross-client/policy regressions. GPU hardware execution remains not_run. The
permanent checkout retains ignored private assets/credentials, and its actual
TLS runtime gate passed all nine checks again after relocation.
