#!/usr/bin/env python3
"""Sync pinned versions from pyproject.toml into .pre-commit-hooks.yaml.

Reads the [project.optional-dependencies] hooks list from pyproject.toml,
extracts the pinned package==version entries, and rewrites every
additional_dependencies list in .pre-commit-hooks.yaml to match.

Rules:
  - Every hook gets the ansible-dev-tools pin.
  - The build-import hook additionally gets the galaxy-importer pin.
"""

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
HOOKS_YAML = REPO_ROOT / ".pre-commit-hooks.yaml"

BUILD_IMPORT_ID = "build-import"


def parse_pins(pyproject_path: Path) -> dict[str, str]:
    """Return {package_name: 'package==version'} from pyproject.toml hooks extra."""
    with open(pyproject_path, "rb") as fh:
        data = tomllib.load(fh)

    pins: dict[str, str] = {}
    for entry in data["project"]["optional-dependencies"]["hooks"]:
        match = re.match(r"^([a-zA-Z0-9_-]+)==(.+)$", entry.strip())
        if match:
            pins[match.group(1).lower()] = entry.strip()
    return pins


def build_dep_string(pins: dict[str, str], hook_id: str) -> str:
    """Build the YAML additional_dependencies value for a given hook."""
    adt_pin = pins.get("ansible-dev-tools")
    gi_pin = pins.get("galaxy-importer")

    if not adt_pin:
        print("ERROR: ansible-dev-tools pin not found in pyproject.toml", file=sys.stderr)
        sys.exit(1)

    if hook_id == BUILD_IMPORT_ID:
        if not gi_pin:
            print("ERROR: galaxy-importer pin not found in pyproject.toml", file=sys.stderr)
            sys.exit(1)
        return f"['{adt_pin}', '{gi_pin}']"

    return f"['{adt_pin}']"


def sync(pyproject_path: Path, hooks_path: Path) -> bool:
    """Sync versions and return True if any changes were made."""
    pins = parse_pins(pyproject_path)
    content = hooks_path.read_text()
    original = content

    lines = content.splitlines(keepends=True)
    result: list[str] = []
    current_hook_id: str | None = None

    for line in lines:
        id_match = re.match(r"^- id:\s+(.+)$", line)
        if id_match:
            current_hook_id = id_match.group(1).strip()

        dep_match = re.match(r"^(\s+additional_dependencies:\s+)(.+)$", line)
        if dep_match and current_hook_id is not None:
            prefix = dep_match.group(1)
            new_value = build_dep_string(pins, current_hook_id)
            line = f"{prefix}{new_value}\n"

        result.append(line)

    new_content = "".join(result)
    if new_content != original:
        hooks_path.write_text(new_content)
        return True
    return False


def main() -> None:
    changed = sync(PYPROJECT, HOOKS_YAML)
    if changed:
        print("Updated .pre-commit-hooks.yaml with versions from pyproject.toml")
    else:
        print(".pre-commit-hooks.yaml is already in sync")


if __name__ == "__main__":
    main()
