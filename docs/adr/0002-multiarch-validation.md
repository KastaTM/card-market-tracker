# ADR-0002: Multiarch container validation

## Context

The production target is Raspberry Pi ARM64, while contributors and CI may run AMD64. P0 must prove the same one-shot capabilities can build and execute on both architectures without claiming physical Pi readiness.

## Decision

Use one Dockerfile and a CI platform matrix for `linux/amd64` and `linux/arm64`. Build each image with Buildx, run version and valid/invalid diagnostic smoke tests, and check effective UID is non-root. CI installs QEMU for ARM64 emulation. Compose offers separate one-shot `version` and `diagnose` commands; it publishes no ports or artificial service healthcheck.

## Alternatives

AMD64-only CI would miss ARM64 build/runtime defects. Requiring physical Pi hardware for every PR is not currently available or reproducible. A long-running no-op container would create misleading health evidence.

## Consequences

Emulation gives early compatibility evidence but cannot measure Pi-specific performance, storage, power, or continuous-operation behavior. Those require native validation in P9.5. CI outcomes must be cited by commit and URL before a gate is marked PASS.

## Status

Accepted for P0 implementation; CI execution evidence remains a separate gate.

## Revisit conditions

Revisit for native ARM64 runners, physical Pi qualification, or a real continuous service with a meaningful healthcheck.
