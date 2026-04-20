# CONTRIBUTING

## Workflow

1. Read [docs/START_HERE.md](/C:/Projects/open-clodex-iflow/docs/START_HERE.md) and [docs/READ_FIRST.md](/C:/Projects/open-clodex-iflow/docs/READ_FIRST.md).
2. Keep documentation, runtime behavior, and tests aligned.
3. Add or update failing tests before changing behavior.
4. Run `make check` before claiming the work is ready.

## Pull requests

- Keep scope narrow and explicit.
- Include verification evidence, not just intent.
- Document deferred work plainly.
- Do not overclaim provider compatibility or guide parity.

## Runtime-specific rules

- Preserve the `/solo` privacy boundary.
- Do not silently weaken `/orch` semantics.
- Treat provider auth/session reuse as environment-dependent truth.
- Keep `windowed` vs `headless` wording honest in docs.
