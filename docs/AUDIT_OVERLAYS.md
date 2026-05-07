# Audit Overlays

This document defines the project-native reviewer overlay layer for `open-clodex-iflow`.

The base methodology references are:

- `affaan-m/everything-claude-code`: cross-harness packaging, skill catalog, selective install discipline.
- `obra/superpowers`: generic engineering workflow discipline such as brainstorming, planning, TDD, debugging, and verification.

These projects are references only. They are not bundled dependencies, installers, global hooks, or hidden runtime requirements.

## Layer Model

- Generic methodology layer: external references that help shape operator process.
- Project overlay layer: repo-native audit/review templates under `overlays/`.
- Runtime layer: `/solo`, `/orch`, lane presets, provider adapters, packets, and artifacts.

The overlay layer is intentionally small. It exists where `open-clodex-iflow` has product-specific value that generic methodology packs do not cover:

- repo forensics against docs/runtime truth,
- tests-of-tests and false-green detection,
- release go/no-go review,
- normalized reviewer packet generation.

## Required Overlays

- `overlays/repo-forensics-review.md`
- `overlays/test-forensics-audit.md`
- `overlays/release-risk-gate.md`
- `overlays/reviewer-packet.md`

Each overlay must define:

- trigger,
- permission boundary,
- required evidence,
- output format,
- non-goals.

## Enforcement

`scripts/validate_overlays.py` checks that all required overlays exist and include the required contract sections. It is part of `make check` through the `enforce` target.

## Runtime Boundary

These overlays are templates and contracts. They are not installed as Codex, Claude, OpenCode, or iFlow plugins by default.

Promotion into a real plugin/skill package requires a separate issue, security review, and docs update.
