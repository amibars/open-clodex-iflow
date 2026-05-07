# release-risk-gate

Purpose: read-only release go/no-go review for open-source publishing and operator use.

## Trigger

Use before tagging a release, publishing to GitHub as ready, or telling an operator the tool is ready for routine use.

## Permission Boundary

Read-only. Do not create tags, releases, package uploads, or public announcements from this overlay.

## Required Evidence

- Current git status and latest commit.
- Local `make check` result.
- GitHub CI result for the pushed commit.
- License, security, contribution, changelog, and release notes state.
- Known deferred scope and whether it is documented.
- Provider compatibility evidence and environment-dependent caveats.

## Output Format

Return:

```text
verdict: proceed | hold | block
release_target:
blocking_findings:
non_blocking_risks:
verification_evidence:
rollback_or_recovery_notes:
deferred_scope:
```

## Non-Goals

- Do not hide provider-dependent failures.
- Do not release if docs overclaim runtime behavior.
- Do not treat local-only provider success as universal provider support.
