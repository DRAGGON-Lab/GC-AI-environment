# Deployment verification evidence

Baseline: `059eff4e5b1906184fe2eee29089693c66e65597` of `cvtalrc/GC-AI-environment`. Source/configuration and Docker checks were executed on 2026-11-21 and 2026-11-23. This is synthetic CI evidence, not an operator migration or credential-rotation receipt.

Local checks on macOS: nine `unittest` configuration/security regressions pass, including rendered local/hosted networks, consumer-owned private secret copies, restricted MySQL health credentials, and complete legacy initialization before export. Python compilation, shell syntax and `git diff --check` pass. Local Docker remains unavailable (missing daemon socket); actual containers ran on GitHub's Docker-capable runners.

| Executed check | Result / evidence |
| --- | --- |
| Fresh MySQL initialization and grants | [Passed](https://github.com/Gonza10V/GC-AI-environment/actions/runs/45165181038): registry import, consumed SELECT1, application SELECT, rejected INSERT, no remote root accounts |
| Digest-pinned synthetic legacy import | Same passing workflow: stopped fake-byte checkpoint image, delayed SQL initialization in isolated MySQL, exact exported bytes/data and checksums, no accounts/grants/secrets in dump, cleanup of containers/anonymous volumes/staging |
| Proxy/network/authentication | Same passing workflow: actual published TLS443, unauthenticated401 with challenge, authenticated frontend/API200, request-size413, sanitized upstream503. Only the proxy joins the normal edge network; backend/database stay internal with no host ports. Uses a clearly identified stdlib backend stub |
| Full production-image hosted integration | [Passed](https://github.com/Gonza10V/GC-AI-environment/actions/runs/45167901039), application `ea6348ac25ebc8a5ebc494e3630873c9bed294ac`, environment `18befe0513f92d735666b313406a939f2db0375b`: built reviewed application images, authenticated wire create/convert with exact formats/sequences/coordinates, rejected unsafe Origin, real MySQL connector/readiness with mocked detector, backup/restore and production janitor command |

The sanitized receipt and exact image identities are committed under [verification/hosted-smoke.json](verification/hosted-smoke.json); [application grants](verification/application-grants.txt) show only USAGE and SELECT on `iGEM2024.parts`. Source/image identities describe the executed CI snapshot. Subsequent documentation-only receipt updates do not change its tested runtime configuration.

Actual failures found and corrected before acceptance: MySQL/Nginx consumer secret readability; MySQL init scripts needing source scope; root account restriction; root-over-TCP health authentication; temporary MySQL initialization being mistaken for completed import; and Docker requiring a non-internal gateway network to publish proxy ports. Follow-up tests cover these boundaries rather than treating rendered configuration as proof of runtime success.

The checkpoint fixtures are deliberately synthetic. CI does not establish real checkpoint deserialization/detector output, GPU execution, real legacy-registry migration, production readiness, deployed credential rotation, browser conversion with the real detector, or operator acceptance. The final application image run after the EXIF-only camera compatibility refinement is recorded on the coordinated application PR.

Required operator receipt: approved source revisions and actual published image digests, checkpoint/registry provenance and import hashes, live authenticated inference/readiness/create/convert, frontend retry, least-privilege grants, backup/restore result, janitor result, denied old credentials after real rotation, and rollback location. Record no secret values. Keep issue #16 and Epic #7 open until the environment PR and these gates are accepted.
