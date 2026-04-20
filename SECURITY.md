# SECURITY

## Reporting a vulnerability

Do not open a public issue for:

- leaked credentials
- provider-account abuse paths
- auth/session reuse bypasses
- secret-handling bugs
- unsafe subprocess execution boundaries

Report security-sensitive findings privately to the maintainer first and include:

- affected file or command
- proof of impact
- reproduction steps
- whether the issue is local-only or cross-machine

## Scope

The most security-sensitive surfaces in this repo are:

- provider override configuration
- local CLI/session reuse
- subprocess execution and prompt handoff
- secret scanning and enforcement tooling

## Expectations

- give enough evidence to reproduce
- avoid posting secrets in reports
- allow a reasonable fix window before public disclosure
