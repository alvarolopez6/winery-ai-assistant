"""Repository hygiene checks that run in CI."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "data",
    "backups",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}

SUSPICIOUS = [
    re.compile(r"IGAA[A-Za-z0-9_-]{20,}"),
    re.compile(r"EAA[A-Za-z0-9]{40,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}"),
    re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com"),
]


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name in {".env", "package-lock.json"}:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".bundle"}:
            continue
        yield path


def test_env_example_exists() -> None:
    assert (ROOT / ".env.example").is_file()


def test_env_is_not_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files", ".env"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""


def test_no_obvious_secrets_or_dead_tunnels() -> None:
    findings: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SUSPICIOUS:
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {pattern.pattern}")
    assert findings == [], "\n".join(findings)
