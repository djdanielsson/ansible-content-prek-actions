#!/usr/bin/env python3
"""Sync pinned versions from pyproject.toml into .pre-commit-hooks.yaml and README.md.

Reads the [project.optional-dependencies] from pyproject.toml and rewrites:

  1. Every additional_dependencies list in .pre-commit-hooks.yaml
  2. All version callouts in README.md (inline references, rev: tags, etc.)

Dependency groups in pyproject.toml:
  - "hooks"            -> ansible-dev-tools pin (used by most hooks)
  - "galaxy-importer"  -> galaxy-importer pin (isolated, conflicts with ansible-dev-tools)
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
README = REPO_ROOT / "README.md"

GALAXY_IMPORTER_ID = "galaxy-importer"


def parse_pins(pyproject_path: Path) -> dict[str, str]:
    """Return {package_name: 'package==version'} from pyproject.toml optional-deps."""
    with open(pyproject_path, "rb") as fh:
        data = tomllib.load(fh)

    pins: dict[str, str] = {}
    opt_deps = data["project"]["optional-dependencies"]
    for group in opt_deps.values():
        for entry in group:
            match = re.match(r"^([a-zA-Z0-9_-]+)==(.+)$", entry.strip())
            if match:
                pins[match.group(1).lower()] = entry.strip()
    return pins


def get_version(pins: dict[str, str], package: str) -> str:
    """Extract just the version string from a pin like 'pkg==1.2.3'."""
    pin = pins.get(package, "")
    return pin.split("==", 1)[1] if "==" in pin else ""


def build_dep_string(pins: dict[str, str], hook_id: str) -> str:
    """Build the YAML additional_dependencies value for a given hook."""
    adt_pin = pins.get("ansible-dev-tools")
    gi_pin = pins.get("galaxy-importer")

    if hook_id == GALAXY_IMPORTER_ID:
        if not gi_pin:
            print("ERROR: galaxy-importer pin not found in pyproject.toml", file=sys.stderr)
            sys.exit(1)
        return f"['{gi_pin}']"

    if not adt_pin:
        print("ERROR: ansible-dev-tools pin not found in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    return f"['{adt_pin}']"


def sync_hooks(pins: dict[str, str], hooks_path: Path) -> bool:
    """Sync .pre-commit-hooks.yaml and return True if changes were made."""
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


def sync_readme(pins: dict[str, str], readme_path: Path) -> bool:
    """Sync version references in README.md and return True if changes were made."""
    content = readme_path.read_text()
    original = content

    adt_version = get_version(pins, "ansible-dev-tools")
    gi_version = get_version(pins, "galaxy-importer")

    if not adt_version:
        print("ERROR: ansible-dev-tools version not found", file=sys.stderr)
        sys.exit(1)

    content = re.sub(
        r"ansible-dev-tools==[\d.]+",
        f"ansible-dev-tools=={adt_version}",
        content,
    )

    if gi_version:
        content = re.sub(
            r"galaxy-importer==[\d.]+",
            f"galaxy-importer=={gi_version}",
            content,
        )

    content = re.sub(
        r"(rev:\s+)v[\d.]+",
        rf"\g<1>v{adt_version}",
        content,
    )

    content = re.sub(
        r'(rev\s*=\s*")v[\d.]+"',
        rf'\g<1>v{adt_version}"',
        content,
    )

    if content != original:
        readme_path.write_text(content)
        return True
    return False


def main() -> None:
    pins = parse_pins(PYPROJECT)
    changed_hooks = sync_hooks(pins, HOOKS_YAML)
    changed_readme = sync_readme(pins, README)

    if changed_hooks:
        print("Updated .pre-commit-hooks.yaml")
    if changed_readme:
        print("Updated README.md")
    if not changed_hooks and not changed_readme:
        print("Everything is already in sync")


if __name__ == "__main__":
    main()
