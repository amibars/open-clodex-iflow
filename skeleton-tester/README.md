# Skeleton Tester

This directory documents the standalone negative-validation harness for the repository enforcement layer.

Run:

```powershell
python scripts/run_skeleton_tester.py
```

What it proves:

- forbidden imports are detected
- layer violations are detected
- secret scanning detects hardcoded tokens
- TDD guard blocks unmapped source files

The harness creates temporary throwaway workspaces outside the main repository path and removes them after the run.
