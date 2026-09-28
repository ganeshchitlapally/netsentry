"""Provenance metadata stamped into every results file."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from netsentry.config import REPO_ROOT


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def provenance(script: str) -> dict[str, Any]:
    """Which script, commit and interpreter produced a result.

    ``git_dirty`` ignores results/ itself, so regenerating results on a clean checkout
    of the code reports a clean tree.
    """
    status = _git("status", "--porcelain", "--", ".", ":(exclude)results")
    return {
        "script": script,
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(status) if status is not None else None,
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
