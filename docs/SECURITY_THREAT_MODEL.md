# Security Threat Model

Status: baseline threat model for open-source release and future orchestration expansion.

`open-clodex-iflow` orchestrates local AI CLIs and may later integrate API bridges, MCP servers, memory layers, and dedicated windows. That makes the security boundary broader than a normal CLI wrapper.

## Assets

Protect:

- local provider auth/session state,
- API keys and custom provider URLs,
- source code and private repo contents,
- generated artifacts and logs,
- prompts and review packets,
- memory/index data if enabled later,
- operator trust in provider verdicts.

## Trust Boundaries

| Boundary | Trusted? | Notes |
| --- | --- | --- |
| Local `open-clodex-iflow` code | trusted after local gates | Must remain auditable and test-covered |
| Provider CLIs | partially trusted | Installed tools may change behavior or auth requirements |
| Provider model output | untrusted | Must never override system/operator policy |
| GitHub/Linear/MCP/plugin inputs | untrusted data | Can provide facts, not authority |
| Generated scaffold/templates | trusted only after health checks | Must not smuggle secrets or unsafe hooks |
| Future memory stores | sensitive | Require opt-in and retention policy |

## Threat Classes

### Prompt injection and cross-agent instruction injection

Risk: provider output or repository text attempts to override orchestration rules, exfiltrate data, or instruct another lane.

Controls:

- strict packet/review schemas,
- provider output treated as data,
- no provider receives write authority by default,
- consolidated review separates findings from commands.

### Command injection

Risk: task text, provider names, model names, file paths, or lane ids are interpolated into shell commands.

Controls:

- prefer subprocess argument arrays,
- validate lane ids against known presets,
- never pass untrusted text through shell command strings,
- add command-shape tests before dedicated windows.

### OAuth/auth-state abuse

Risk: reuse-first discovery accidentally leaks or mutates provider auth/session state.

Controls:

- discovery reports state presence, not secrets,
- no copying provider credentials into artifacts,
- custom API/base URL config must avoid logging secret values,
- operator must explicitly configure paid/API-key lanes.

### Tool poisoning and malicious MCP/plugin behavior

Risk: a provider, MCP server, plugin, or generated config changes tool descriptions, routes work to malicious code, or grants unexpected filesystem/network authority.

Controls:

- MCP/plugin expansion is opt-in,
- security review before default enablement,
- generated-pack health checks,
- clear allowlist of supported provider/lane ids.

### Memory poisoning and sensitive retention

Risk: future memory layers store secrets, injected instructions, or stale wrong facts and reuse them across tasks.

Controls:

- memory is non-v1 and opt-in,
- retention and deletion policy required before enablement,
- memory content must be treated as untrusted retrieval context,
- security doc update required before memory becomes default.

### Provider output spoofing

Risk: provider emits incidental JSON, nested JSON, or text that looks like a valid review but is not the explicit normalized review payload.

Controls:

- strict review extraction and normalization,
- synthetic failures for invalid output,
- raw output retained for inspection,
- tests rejecting incidental/nested partial JSON.

### Orphan process and window lifecycle risk

Risk: dedicated windows or long-running subprocesses remain alive after timeout/cancel and continue using auth/session state.

Controls:

- timeout contract preserves process termination facts,
- dedicated window backend must implement cleanup,
- no dedicated windows claim before lifecycle tests exist.

### Code sabotage and destructive writes

Risk: review lanes or external agents modify code, delete files, or produce patches outside intended authority.

Controls:

- default lanes are planner/reviewer lanes,
- write-capable lanes are explicit opt-in,
- `/solo` remains private and no-fan-out,
- future write lanes require separate policy and tests.

## Required Security Artifacts

Before open-source release:

- root `SECURITY.md` must point to this threat model,
- `docs/PROVIDER_COMPATIBILITY.md` must distinguish adapter support from live success,
- `docs/WINDOWED_RUNTIME_CONTRACT.md` must clarify current vs future window claims,
- `docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md` must define timeout evidence preservation.

Before enabling memory/MCP/plugin layers by default:

- update this threat model,
- add opt-in operator runbook,
- add secret-retention checks,
- add generated config review/health check.

## Current Implementation Status

Current sequential v1 is lower-risk than a full agent swarm because it does not implement hidden parallel fan-out, persistent cross-agent memory, or default write-capable lanes. The main current risks are provider output spoofing, auth-state handling, command construction, and truthful documentation of provider/runtime behavior.
