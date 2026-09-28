"""Fetch and verify the UNSW-NB15 CSVs.

The official host (a UNSW SharePoint folder) rejects scripted downloads (HTTP 403),
so files are downloaded in a browser and then imported with ``--from``. Integrity is
checked against SHA-256 hashes pinned from the official files on 2026-09-28. UNSW
does not publish checksums, so these are "pinned at first download", not official.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

OFFICIAL_PAGE = "https://research.unsw.edu.au/projects/unsw-nb15-dataset"
OFFICIAL_FOLDER = (
    "https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/"
    "EnuQZZn3XuNBjgfcUu4DIVMBLCHyoLHqOswirpOQifr1ag?e=gKWkLS"
)


@dataclass(frozen=True)
class DataFile:
    name: str
    folder: str  # location inside the official SharePoint folder
    sha256: str
    size_bytes: int
    required: bool = True


FILES: tuple[DataFile, ...] = (
    DataFile(
        "UNSW_NB15_training-set.csv",
        "CSV Files/Training and Testing Sets",
        "bec7dd5ec88dc2a0ccc7a07879d338395ed7421750f675fd0339e07dfe0648fa",
        32_293_018,
    ),
    DataFile(
        "UNSW_NB15_testing-set.csv",
        "CSV Files/Training and Testing Sets",
        "734fe6642edf758f7c94d7d9149426b49d202fe8e7bf0bef47392489c3c0a559",
        15_380_800,
    ),
    DataFile(
        "NUSW-NB15_features.csv",
        "CSV Files",
        "c55f19cceebb6360dc50f44f8a5f246ccefbcf8a6c604ac1ad46e643869cafce",
        4_044,
        required=False,
    ),
)


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def verify(raw_dir: Path, files: tuple[DataFile, ...] = FILES) -> dict[str, str]:
    """Return {file name: status}; status is 'ok', 'missing' or 'checksum mismatch'."""
    status: dict[str, str] = {}
    for f in files:
        path = raw_dir / f.name
        if not path.is_file():
            status[f.name] = "missing"
        elif path.stat().st_size != f.size_bytes or sha256_of(path) != f.sha256:
            status[f.name] = "checksum mismatch"
        else:
            status[f.name] = "ok"
    return status


def import_from(source_dir: Path, raw_dir: Path, files: tuple[DataFile, ...] = FILES) -> list[str]:
    """Copy any expected files found in ``source_dir`` into ``raw_dir``. Returns names copied."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for f in files:
        src = source_dir / f.name
        if src.is_file():
            shutil.copy2(src, raw_dir / f.name)
            copied.append(f.name)
    return copied


def manual_instructions(raw_dir: Path) -> str:
    lines = [
        "UNSW-NB15 must be downloaded manually (the official host blocks scripted access).",
        f"  1. Open the official folder: {OFFICIAL_FOLDER}",
        f"     (linked from {OFFICIAL_PAGE})",
        "  2. Download these files:",
    ]
    for f in FILES:
        opt = "" if f.required else "  (optional: official feature descriptions)"
        lines.append(f"       UNSW-NB15 dataset/{f.folder}/{f.name}{opt}")
    lines += [
        f"  3. Either copy them into {raw_dir}/ or run:",
        "       uv run python scripts/download_data.py --from <your download folder>",
        "     (from WSL, Windows Downloads is /mnt/c/Users/<you>/Downloads)",
    ]
    return "\n".join(lines)
