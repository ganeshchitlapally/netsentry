"""Obtain and verify the UNSW-NB15 CSVs.

Usage:
    uv run python scripts/download_data.py                   # verify data/raw
    uv run python scripts/download_data.py --from ~/Downloads  # import, then verify

Exits non-zero (with manual download instructions) if a required file is missing
or fails its checksum.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from netsentry.config import REPO_ROOT, load_config
from netsentry.data.download import FILES, import_from, manual_instructions, verify


def main() -> int:
    cfg = load_config("data")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="source", type=Path, help="folder holding downloaded CSVs")
    parser.add_argument("--raw-dir", type=Path, default=REPO_ROOT / cfg["raw_dir"])
    args = parser.parse_args()

    if args.source:
        copied = import_from(args.source.expanduser(), args.raw_dir)
        print(f"Imported from {args.source}: {copied or 'nothing'}")

    status = verify(args.raw_dir)
    required = {f.name for f in FILES if f.required}
    for name, state in status.items():
        tag = "" if name in required else " (optional)"
        print(f"  {state:>17}  {name}{tag}")

    if any(status[n] != "ok" for n in required):
        print("\n" + manual_instructions(args.raw_dir), file=sys.stderr)
        return 1
    print("All required UNSW-NB15 files present and verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
