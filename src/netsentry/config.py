"""Repository paths and YAML config loading.

Paths resolve from the repo root so scripts behave the same regardless of the
current working directory. Set ``NETSENTRY_ROOT`` to override (e.g. in Docker,
where the package is installed non-editable).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(os.environ.get("NETSENTRY_ROOT", Path(__file__).resolve().parents[2]))
CONFIG_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
RESULTS_DIR = REPO_ROOT / "results"


def load_config(name: str, config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    """Load ``configs/<name>.yaml`` as a dict.

    Raises:
        FileNotFoundError: if the config file does not exist.
        ValueError: if the file does not contain a YAML mapping.
    """
    path = config_dir / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config {path} must be a YAML mapping, got {type(cfg).__name__}")
    return cfg
