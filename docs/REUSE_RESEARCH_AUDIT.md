# Reuse Research Audit

Date: 2026-05-01

Scope: GitHub starred projects relevant to `open-clodex-iflow` as a Windows-first, reuse-first CLI orchestrator with visible/default runtime, strict packets, and optional future memory/security/observability layers.

This is a reference audit, not a decision to vendor code. The current v1 product contract remains the local CLI runtime described in `docs/ARCH_SPEC.md`, `docs/ORCHESTRATED.md`, and `docs/PROVIDER_COMPATIBILITY.md`.

## Current Project Baseline

`open-clodex-iflow` currently optimizes for:

- Reusing already installed provider CLIs and their local auth state.
- Running `/solo` with no fan-out.
- Running `/orch` as intake, preflight, sequential provider execution, and consolidated review.
- Keeping provider outputs constrained by `artifact.json`, `review.json`, and `consolidated_review.json`.
- Defaulting to operator-visible behavior while not yet claiming dedicated OS-window spawning.
- Treating parallel debate loops, mailbox routing, and memory as future layers rather than hidden v1 features.

Any external reuse must preserve these boundaries.

## Decision Summary

| Candidate | Decision | Reason |
| --- | --- | --- |
| `router-for-me/CLIProxyAPI` | Study as API-bridge reference, do not make v1 dependency | Strong CLI-auth reuse and OpenAI/Gemini/Claude/Codex-compatible server model, but it expands our v1 from local CLI orchestration into API proxy/server scope. |
| `bfly123/claude_codex_bridge` | Architecture reference only; do not copy code | Best visible multi-agent terminal reference, but license is AGPL-3.0 and current design is broader than our v1. Concepts are useful; code reuse is not safe for permissive open-source release. |
| `GammaLabTechnologies/harmonist` | Adopt ideas for self-checking packs | MIT, strong mechanical protocol enforcement and manifest/health-check concepts. Useful for generated scaffold/reviewer packs. |
| `HKUDS/ClawTeam` | Defer to later swarm audit | Strong swarm/product ambition, but too broad for current sequential v1. Useful after the core runtime is stable. |
| `maslennikov-ig/claude-code-orchestrator-kit` | Compare, but do not depend | Useful Claude Code orchestration and slash-command reference. License and Claude-specific coupling need separate review before reuse. |
| `RuslanKoroy/oc-router` | Use as OpenCode routing reference | Small MIT project directly relevant to OpenCode model/mode routing. Useful for lane config UX, not as a core dependency yet. |
| `zilliztech/memsearch` | Optional future memory backend reference | Strong cross-agent memory concept for Codex/Claude/OpenCode, but Milvus/hooks/config mutation are not v1-safe defaults. |
| `alash3al/stash` | Optional future memory backend reference | Self-hosted Postgres/pgvector MCP memory is deployable, but introduces infrastructure and model dependencies outside v1. |
| `future-agi/future-agi` | Optional eval/observability reference | Good taxonomy for traces, evals, simulations, guardrails, and gateway, but too heavy as built-in v1 infrastructure. |
| `nikolai-vysotskyi/trace-mcp` | Optional repo-intelligence adapter reference | Strong local-first MCP/code graph concept. Do not auto-install or mutate client configs without explicit operator action. |
| `safe-agentic-framework/safe-mcp` | Use for threat-model taxonomy | High-value MCP/agent threat vocabulary for `SECURITY.md` and runtime guardrails. License must be verified before copying structured assets. |
| `joi-lab/cursor-multimodel-review` | Prompt/reference only | Relevant adversarial review pattern, but Cursor-specific and too small to drive architecture. |

## High-Value Findings

### 1. Visible multi-agent runtime needs a mailbox/attempt model before true fan-out.

`claude_codex_bridge` is the closest match to the desired "visible agents in terminal panes" workflow. The useful concept is not its UI itself; it is the separation between:

- agent endpoint identity,
- mailbox message,
- delivery attempt,
- provider runtime fact,
- reply record,
- timeout/inspection result.

That maps cleanly to a future `open-clodex-iflow` layer:

- `LaneEndpoint`
- `ReviewMessage`
- `AttemptRecord`
- `ProviderRun`
- `ReviewRecord`
- `ConsolidatedReview`

This should be documented before implementing parallel fan-out. Without it, parallel lanes will quickly become ad-hoc subprocess management.

### 2. Timeout semantics should be "inspectable incomplete", not blind failure.

The strongest runtime lesson from `claude_codex_bridge` is that a timeout does not necessarily mean the provider failed. It can mean:

- the process is still working,
- the UI accepted the task but no final response was captured,
- the runtime lost capture visibility,
- the provider produced partial output before the timeout.

For `open-clodex-iflow`, timeout records should preserve:

- lane id,
- provider,
- command shape,
- start/end timestamps,
- captured stdout/stderr tail,
- whether the provider process was terminated,
- whether the attempt is retryable,
- operator-facing inspection hint.

This supports the current docs promise of honest provider-dependent truth.

### 3. Dedicated OS-window spawning is a separate subsystem, not a small flag.

CCB's Windows notes point to a real mux/window backend contract. For our project, "windowed" should not be silently redefined as "real OS panes" until we have:

- capability detection,
- backend contract,
- pane/process lifecycle,
- command injection boundaries,
- capture semantics,
- cleanup/kill behavior,
- Windows Terminal or psmux trade-off documented.

Current v1 should keep saying: visible/sequential provider output is implemented; dedicated OS-window worker lanes are deferred.

### 4. API bridge is valuable, but should remain optional.

`CLIProxyAPI` is highly relevant to reuse-first auth because it wraps installed CLIs into compatible APIs and has runtime executors for provider-specific behavior. The risk is product shape: importing that direction too early turns `open-clodex-iflow` into an API proxy/control plane before the local CLI orchestrator is done.

Recommended stance:

- v1: keep direct CLI orchestration.
- v1.x: add an optional adapter backend for API-compatible provider endpoints.
- later: evaluate whether a CLI-proxy mode belongs inside this repo or as a separate companion.

### 5. OpenCode model/mode routing deserves a first-class lane config.

`oc-router` is small, but the problem it targets is exactly relevant: OpenCode model selection and routing should not depend on users remembering flags.

For `open-clodex-iflow`, the right UX is:

- operator selects lane presets by name,
- lane presets encode provider, model, mode, and thinking capability,
- CLI exposes clear toggles and overrides,
- defaults remain safe planner/reviewer lanes.

This matches the existing `default-planners` and `recommended-planners` model.

### 6. Generated packs should be self-verifying.

`harmonist` is useful because it treats an agent pack as something that can be mechanically checked. The transferable idea is a generated-pack health check:

- required files exist,
- manifest matches files,
- reviewer profiles are indexed,
- templates render,
- docs and task contracts are synchronized,
- no generated pack claims capabilities absent from runtime.

This fits the Iron Dome enforcement style already used by this repo.

### 7. Memory should be optional and explicit.

`memsearch`, `stash`, and `trace-mcp` all point toward a valuable future: persistent context and code intelligence across Codex, Claude, OpenCode, and other workers.

They should not be default v1 behavior because they introduce one or more of:

- local config mutation,
- hooks in external CLIs,
- vector database infrastructure,
- extra model/API dependencies,
- sensitive memory retention concerns.

Recommended stance: add memory as an opt-in adapter family with an explicit threat model and operator approval.

### 8. Security docs should use an agent/MCP threat taxonomy.

`safe-mcp` is useful as vocabulary for risks that are easy to miss in an orchestrator:

- tool poisoning,
- prompt injection,
- over-privileged tool abuse,
- command injection,
- OAuth phishing,
- credential persistence,
- memory poisoning,
- cross-agent instruction injection,
- autonomous loop exploit,
- code sabotage,
- data destruction.

`open-clodex-iflow` should turn this into a practical `SECURITY.md` plus runtime guardrails, not a theoretical appendix.

## Concrete Follow-Up Work

These are the next useful docs/tasks before expanding runtime scope:

1. Add `docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md`.
   Define attempt state, timeout behavior, partial-output preservation, retry policy, and operator inspection output.

2. Add `docs/WINDOWED_RUNTIME_CONTRACT.md`.
   Define current visible sequential mode vs future dedicated OS-window spawning, including Windows backend candidates and capability gates.

3. Add `docs/SECURITY_THREAT_MODEL.md`.
   Cover CLI reuse, OAuth/auth-state boundaries, provider subprocesses, prompt injection, MCP/plugin risks, and memory risks.

4. Add a generated-pack health check.
   Use a Harmonist-style manifest/check loop for scaffold templates and reviewer/lane packs.

5. Keep `CLIProxyAPI` as optional backend research.
   Do not merge API proxy scope into v1 until the local CLI path is stable.

6. Keep CCB as architecture reference only.
   Do not copy source code because of AGPL-3.0 unless the whole licensing strategy intentionally changes.

7. Add OpenCode lane UX tasks.
   Make model/mode/thinking choices discoverable through named lane presets and slash-style/toggle-friendly CLI help.

## Explicit Non-Goals For Current v1

- No hidden AGPL code reuse.
- No implicit API server.
- No automatic installation of memory hooks or MCP servers.
- No claim that current `windowed` equals dedicated external OS panes.
- No parallel debate loop until message, attempt, timeout, and aggregation contracts are written.

## Source Notes

Primary evidence came from GitHub repository metadata and selected repository files for the candidates above, plus the local `open-clodex-iflow` docs and runtime contracts. The in-app browser was initialized for this research, but GitHub navigation hit an app auth-token limitation, so GitHub connector/API reads were used as the reliable source.
