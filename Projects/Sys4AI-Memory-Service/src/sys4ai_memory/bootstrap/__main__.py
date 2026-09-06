"""Installed-package consumer preparation command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .prepare import prepare_project_memory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="prepare project-local canonical memory files")
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--project-id", required=True)
    prepare.add_argument("--project-name", required=True)
    prepare.add_argument("--principal-id", required=True)
    prepare.add_argument("--allow-source-registration", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = prepare_project_memory(
            args.project_root,
            args.project_id,
            args.project_name,
            args.principal_id,
            allow_source_registration=args.allow_source_registration,
        )
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        return 2
    print(json.dumps(result.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
