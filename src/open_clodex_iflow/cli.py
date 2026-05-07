from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable

from open_clodex_iflow.adapters.discovery import discover_cli_state
from open_clodex_iflow.contracts import new_trace_id, write_json
from open_clodex_iflow.lanes import (
    DEFAULT_LANE_SET_ID,
    render_lane_catalog,
    supported_lane_set_ids,
)
from open_clodex_iflow.orchestration.preflight import build_artifact_packet
from open_clodex_iflow.orchestration.runtime import run_orchestration
from open_clodex_iflow.scaffold.bootstrap import scaffold_workspace


def normalize_aliases(argv: Iterable[str]) -> list[str]:
    normalized = list(argv)
    if not normalized:
        return normalized

    aliases = {
        "/solo": "solo",
        "/orch": "orch",
        "/orchester": "orch",
        "/lanes": "lanes",
        "/clean": "clean",
    }
    if normalized[0] in aliases:
        normalized[0] = aliases[normalized[0]]
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="open-clodex-iflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solo = subparsers.add_parser("solo", help="Private Codex-only mode")
    solo.add_argument("task", nargs="?", default="", help="Optional task summary")
    solo.add_argument(
        "--output-dir",
        type=Path,
        help="Directory where artifact.json should be written",
    )

    orch = subparsers.add_parser("orch", help="Orchestrated fan-out mode")
    orch.add_argument("task", nargs="?", default="", help="Optional orchestration task")
    orch.add_argument(
        "--mode",
        choices=["windowed", "headless", "dedicated-windows"],
        default="windowed",
        help="Worker execution mode; windowed streams in the current terminal, dedicated-windows opens OS windows on Windows",
    )
    orch.add_argument(
        "--output-dir",
        type=Path,
        help="Directory where artifact.json and consolidated_review.json should be written",
    )
    provider_selection = orch.add_mutually_exclusive_group()
    provider_selection.add_argument(
        "--providers",
        help="Comma-separated provider list to execute (defaults to all runnable adapters)",
    )
    provider_selection.add_argument(
        "--lanes",
        help="Comma-separated lane preset IDs to execute",
    )
    orch.add_argument(
        "--lane-set",
        choices=supported_lane_set_ids(),
        help="Named lane set to execute when --providers/--lanes are not supplied",
    )
    orch.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Maximum runtime per provider execution",
    )
    orch.add_argument(
        "--execution",
        choices=["sequential", "parallel"],
        default="sequential",
        help="Lane execution strategy; defaults to stable sequential execution",
    )
    orch.add_argument(
        "--hold-windows-seconds",
        type=int,
        default=0,
        help="Keep dedicated worker windows open for N seconds after each lane exits",
    )

    subparsers.add_parser("doctor", help="Inspect installed CLIs and known local state")
    subparsers.add_parser("lanes", help="List available lane presets and CLI toggles")
    scaffold = subparsers.add_parser("scaffold", help="Bootstrap an Iron Dome starter workspace")
    scaffold.add_argument("destination", type=Path, help="Target directory for the new workspace")
    scaffold.add_argument(
        "--force",
        action="store_true",
        help="Overwrite known scaffold files when the destination is not empty",
    )
    clean = subparsers.add_parser("clean", help="Prune local .open-clodex-iflow trace directories")
    clean.add_argument(
        "--root",
        type=Path,
        help="Trace root to clean; defaults to .open-clodex-iflow under the current directory",
    )
    clean.add_argument(
        "--keep-last",
        type=int,
        default=20,
        help="Number of newest trace-* directories to keep",
    )
    clean.add_argument(
        "--yes",
        action="store_true",
        help="Actually delete old trace directories; without this flag clean is a dry-run",
    )

    return parser


def default_session_dir(trace_id: str) -> Path:
    return Path.cwd() / ".open-clodex-iflow" / trace_id


def reserve_trace_safe_default_session_dir(trace_id: str) -> Path:
    base_dir = default_session_dir(trace_id)
    for suffix in range(0, 1000):
        candidate = base_dir if suffix == 0 else base_dir.parent / f"{base_dir.name}-{suffix:02d}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"could not reserve trace-safe output directory for {trace_id}")


def trace_root(root: Path | None = None) -> Path:
    return root or Path.cwd() / ".open-clodex-iflow"


def cleanup_trace_dirs(root: Path, *, keep_last: int, dry_run: bool) -> list[Path]:
    if keep_last < 0:
        raise ValueError("--keep-last must be >= 0")
    if not root.exists():
        return []
    trace_dirs = sorted(
        [
            candidate
            for candidate in root.iterdir()
            if candidate.is_dir() and candidate.name.startswith("trace-")
        ],
        key=lambda path: path.name,
        reverse=True,
    )
    removable = trace_dirs[keep_last:]
    if not dry_run:
        for path in removable:
            shutil.rmtree(path)
    return removable


def parse_runtime_args(argv: Iterable[str] | None) -> argparse.Namespace:
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    return build_parser().parse_args(normalize_aliases(raw_argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_runtime_args(argv)

    if args.command == "solo":
        snapshot = discover_cli_state()
        artifact = build_artifact_packet(mode="solo", task=args.task, provider_snapshot=snapshot)
        output_dir = args.output_dir or default_session_dir(artifact.trace_id)
        artifact_path = write_json(output_dir / "artifact.json", artifact)
        print(f"solo preflight complete; artifact written to {artifact_path}")
        return 0

    if args.command == "orch":
        snapshot = discover_cli_state()
        output_dir = args.output_dir or reserve_trace_safe_default_session_dir(new_trace_id())
        artifact, review = run_orchestration(
            task=args.task,
            runtime_mode=args.mode,
            provider_snapshot=snapshot,
            requested_providers=[
                provider.strip()
                for provider in (args.providers or "").split(",")
                if provider.strip()
            ]
            or None,
            requested_lanes=[
                lane.strip()
                for lane in (args.lanes or "").split(",")
                if lane.strip()
            ]
            or None,
            lane_set=None if args.providers else (args.lane_set or DEFAULT_LANE_SET_ID),
            timeout_seconds=args.timeout_seconds,
            execution_mode=args.execution,
            output_dir=output_dir,
            window_hold_seconds=max(0, args.hold_windows_seconds),
        )
        artifact_path = write_json(output_dir / "artifact.json", artifact)
        review_path = write_json(output_dir / "consolidated_review.json", review)
        print(
            "orch runtime complete; "
            f"artifact={artifact_path} consolidated_review={review_path}"
        )
        return 0

    if args.command == "doctor":
        print(json.dumps(discover_cli_state(), indent=2, sort_keys=True))
        return 0

    if args.command == "lanes":
        print(render_lane_catalog())
        return 0

    if args.command == "scaffold":
        created_files = scaffold_workspace(args.destination, force=args.force)
        print(f"scaffolded {len(created_files)} files in {args.destination.resolve()}")
        return 0

    if args.command == "clean":
        root = trace_root(args.root).resolve()
        removed = cleanup_trace_dirs(root, keep_last=args.keep_last, dry_run=not args.yes)
        action = "dry-run; would remove" if not args.yes else "removed"
        print(f"clean {action} {len(removed)} trace dirs under {root}")
        for path in removed:
            print(path)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
