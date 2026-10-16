#!/usr/bin/env python3
"""Decide whether main has releasable changes and calculate a unique tag."""

import re
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
RELEASABLE_PATHS = (
    "hooks",
    ".pre-commit-hooks.yaml",
    "pyproject.toml",
    "README.md",
)
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def adt_version() -> tuple[int, int, int]:
    with PYPROJECT.open("rb") as stream:
        data = tomllib.load(stream)

    for dependency in data["project"]["optional-dependencies"]["hooks"]:
        match = re.fullmatch(r"ansible-dev-tools==(\d+)\.(\d+)\.(\d+)", dependency)
        if match:
            return tuple(int(part) for part in match.groups())

    raise ValueError("ansible-dev-tools must be pinned to a three-part version")


def release_tags() -> list[tuple[int, int, int]]:
    versions = []
    for tag in run_git("tag", "--list", "v*").splitlines():
        match = TAG_PATTERN.fullmatch(tag)
        if match:
            versions.append(tuple(int(part) for part in match.groups()))
    return versions


def has_releasable_changes(versions: list[tuple[int, int, int]]) -> bool:
    if not versions:
        return True

    latest_tag = "v" + ".".join(str(part) for part in max(versions))
    result = subprocess.run(
        ["git", "diff", "--quiet", f"{latest_tag}..HEAD", "--", *RELEASABLE_PATHS],
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("git diff failed while checking for releasable changes")
    return result.returncode == 1


def next_version(
    adt: tuple[int, int, int], existing: list[tuple[int, int, int]]
) -> tuple[int, int, int]:
    if not existing or adt > max(existing):
        return adt

    major, minor, patch = max(existing)
    return major, minor, patch + 1


def main() -> None:
    existing = release_tags()
    if not has_releasable_changes(existing):
        print("release=false")
        return

    adt = adt_version()
    version = next_version(adt, existing)
    tag = "v" + ".".join(str(part) for part in version)
    print("release=true")
    print(f"tag={tag}")
    print(f"adt_version={'.'.join(str(part) for part in adt)}")


if __name__ == "__main__":
    main()
