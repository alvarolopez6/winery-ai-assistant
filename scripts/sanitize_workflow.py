"""Sanitize an n8n workflow export before committing it.

Removes instance-specific metadata and fails when a likely secret is found.

Usage:
    python scripts/sanitize_workflow.py input.json output.json
    python scripts/sanitize_workflow.py --check workflows/main.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TOP_LEVEL_METADATA = {
    "id",
    "versionId",
    "activeVersionId",
    "versionCounter",
    "triggerCount",
    "sourceWorkflowId",
    "shared",
    "meta",
    "staticData",
    "pinData",
}

SUSPICIOUS_PATTERNS = [
    re.compile(r"IGAA[A-Za-z0-9_-]{20,}"),
    re.compile(r"EAA[A-Za-z0-9]{40,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}"),
    re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
]


def sanitize(value: Any, *, inside_credentials: bool = False) -> Any:
    """Return a copy of value with instance-specific metadata removed."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if inside_credentials and key == "id":
                continue
            if key == "webhookId":
                continue
            cleaned[key] = sanitize(
                item,
                inside_credentials=inside_credentials or key == "credentials",
            )
        return cleaned

    if isinstance(value, list):
        return [sanitize(item, inside_credentials=inside_credentials) for item in value]

    return value


def sanitize_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    data = dict(workflow)
    for field in TOP_LEVEL_METADATA:
        data.pop(field, None)
    return sanitize(data)


def find_secrets(value: Any, path: str = "$") -> list[str]:
    """Return JSON paths whose string value looks like a credential."""
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(find_secrets(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_secrets(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern.search(value):
                findings.append(f"{path}: matches {pattern.pattern}")
                break
    return findings


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list) and len(data) == 1:
        data = data[0]
    if not isinstance(data, dict):
        raise TypeError(f"{path} does not contain a single workflow object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument(
        "--check",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="only scan files for likely secrets",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.check:
        failed = False
        for path in args.check:
            findings = find_secrets(load_json(path))
            if findings:
                failed = True
                print(f"{path}: possible secret(s) found")
                for finding in findings:
                    print(f"  - {finding}")
            else:
                print(f"{path}: no obvious secrets")
        return 1 if failed else 0

    if not args.input or not args.output:
        raise SystemExit("input and output are required unless --check is used")

    workflow = sanitize_workflow(load_json(args.input))
    findings = find_secrets(workflow)
    if findings:
        for finding in findings:
            print(f"possible secret: {finding}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(workflow, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"sanitized workflow written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
