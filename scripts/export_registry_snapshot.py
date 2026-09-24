"""Export the live Python catalog for the static GitHub Pages application."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zymepage.catalog import list_registry_groups


def export_snapshot(destination: Path) -> Path:
    payload = {
        "schema_version": "1.0.0",
        "registries": list_registry_groups(),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/data/registry_snapshot.json"),
    )
    arguments = parser.parse_args()
    export_snapshot(arguments.output)


if __name__ == "__main__":
    main()
