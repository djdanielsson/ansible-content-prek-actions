#!/usr/bin/env python3
"""Validate changelog fragments for an Ansible collection.

Adapted from ansible/ansible-content-actions (Apache-2.0).
https://github.com/ansible/ansible-content-actions
"""

import argparse
import logging
import re
import subprocess
import sys

from collections import defaultdict
from pathlib import Path

FORMAT = "[%(asctime)s] - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("validate_changelog")
logger.setLevel(logging.DEBUG)


def is_changelog_file(ref: str) -> bool:
    """Check if a file is a changelog fragment.

    :param ref: the file to be checked
    :returns: True if file is a changelog fragment else False
    """
    match = re.match(r"^changelogs/fragments/(.*)\.(yaml|yml)$", ref)
    return bool(match)


def is_module_or_plugin(ref: str) -> bool:
    """Check if a file is a module or plugin.

    :param ref: the file to be checked
    :returns: True if file is a module or plugin else False
    """
    prefix_list = (
        "plugins/modules",
        "plugins/module_utils",
        "plugins/action",
        "plugins/inventory",
        "plugins/lookup",
        "plugins/filter",
        "plugins/connection",
        "plugins/become",
        "plugins/cache",
        "plugins/callback",
        "plugins/cliconf",
        "plugins/httpapi",
        "plugins/netconf",
        "plugins/shell",
        "plugins/strategy",
        "plugins/terminal",
        "plugins/test",
        "plugins/vars",
        "roles/",
        "playbooks/",
        "meta/runtime.yml",
    )
    return ref.startswith(prefix_list)


def is_release_pr(changes: dict[str, list[str]]) -> bool:
    """Determine whether the changeset looks like a release.

    :param changes: A dictionary keyed on change status (A, M, D, etc.) of lists of changed files
    :returns: True if the changes match a collection release else False
    """
    if not set(changes.keys()).issubset(("D", "M")):
        return False

    if not all(is_changelog_file(x) for x in changes["D"]):
        return False

    if not set(changes["M"]).issubset(
        ("CHANGELOG.rst", "changelogs/changelog.yaml", "galaxy.yml")
    ):
        return False

    return True


def is_changelog_needed(changes: dict[str, list[str]]) -> bool:
    """Determine whether a changelog fragment is necessary.

    :param changes: A dictionary keyed on change status (A, M, D, etc.) of lists of changed files
    :returns: True if a changelog fragment is required for this changeset else False
    """
    modifications = changes["M"] + changes["D"]
    if any(is_module_or_plugin(x) for x in modifications):
        return True

    return False


def is_valid_changelog_format(path: str) -> bool:
    """Check if changelog fragment is formatted properly.

    :param path: the file to be checked
    :returns: True if the file passes validation else False
    """
    import yaml  # noqa: PLC0415 -- deferred so the module can be imported without pyyaml

    try:
        config = Path("changelogs/config.yaml")
        with open(config, "rb") as config_file:
            changelog_config = yaml.safe_load(config_file)
            changes_type = tuple(item[0] for item in changelog_config["sections"])
            changes_type += (changelog_config["trivial_section_name"],)
            changes_type += (changelog_config["prelude_section_name"],)
            logger.info("Found the following changelog sections: %s", changes_type)
    except (OSError, yaml.YAMLError) as exc:
        logger.info(
            "Failed to read changelog config, using default sections instead: %s", exc
        )
        changes_type = (
            "release_summary",
            "breaking_changes",
            "major_changes",
            "minor_changes",
            "removed_features",
            "deprecated_features",
            "security_fixes",
            "bugfixes",
            "known_issues",
            "trivial",
        )

    try:
        with open(path, "rb") as file_desc:
            result = list(yaml.safe_load_all(file_desc))

        for section in result:
            for key in section.keys():
                if key not in changes_type:
                    msg = f"{key} from {path} is not a valid changelog type"
                    logger.error(msg)
                    return False
                if key == "release_summary" and not isinstance(section[key], str):
                    logger.error("release_summary should not be a list")
                    return False
                elif key != "release_summary" and not isinstance(section[key], list):
                    logger.error(
                        "Changelog section %s from file %s must be a list, '%s' found instead.",
                        key,
                        path,
                        type(section[key]),
                    )
                    return False
        return True
    except (OSError, yaml.YAMLError) as exc:
        msg = f"yaml loading error for file {path} -> {exc}"
        logger.error(msg)
        return False


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run a command and return the response.

    :param cmd: The command to run
    :returns: A tuple of (return code, stdout, stderr)
    """
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding="utf-8",
    ) as proc:
        out, err = proc.communicate()
        return proc.returncode, out, err


def _detect_default_ref() -> str:
    """Auto-detect the best base ref to diff against.

    Tries, in order:
      1. origin/HEAD (the remote's default branch)
      2. The current branch's upstream tracking ref
      3. HEAD (compares staged/unstaged changes only)
    """
    # Remote default branch (e.g. origin/main, origin/master)
    ret, out, _ = run_command("git symbolic-ref refs/remotes/origin/HEAD")
    if ret == 0 and out.strip():
        ref = out.strip().removeprefix("refs/remotes/")
        logger.info("Auto-detected remote default branch: %s", ref)
        return ref

    # Current branch's upstream tracking ref
    ret, out, _ = run_command("git rev-parse --abbrev-ref --symbolic-full-name @{u}")
    if ret == 0 and out.strip():
        ref = out.strip()
        logger.info("Auto-detected upstream tracking ref: %s", ref)
        return ref

    logger.info("No remote ref found, falling back to HEAD")
    return "HEAD"


def _resolve_ref(ref: str) -> str:
    """Find a valid git ref, trying origin/<ref> first then <ref> bare.

    :param ref: The base ref name (e.g. "main", "origin/main", "HEAD~1")
    :returns: The first ref that resolves successfully
    """
    candidates = [f"origin/{ref}", ref] if "/" not in ref else [ref]
    for candidate in candidates:
        ret, _, _ = run_command(f"git rev-parse --verify {candidate}")
        if ret == 0:
            logger.info("Resolved ref %r -> %s", ref, candidate)
            return candidate

    logger.error(
        "Could not resolve ref %r. Tried: %s. "
        "Make sure the remote exists (git fetch) or pass a valid ref with --ref.",
        ref,
        ", ".join(candidates),
    )
    sys.exit(1)


def list_files(ref: str) -> dict[str, list[str]]:
    """List all files changed since ref, grouped by change status.

    :param ref: The git ref to compare to
    :returns: A dictionary keyed on change status (A, M, D, etc.) of lists of changed files
    """
    resolved = _resolve_ref(ref)
    command = f"git diff {resolved} --name-status"
    logger.info("Executing -> %s", command)
    ret_code, stdout, stderr = run_command(command)
    if ret_code != 0:
        logger.error("git diff failed: %s", stderr.strip())
        sys.exit(1)

    changes: dict[str, list[str]] = defaultdict(list)
    for file in stdout.split("\n"):
        file_attr = file.split("\t")
        if len(file_attr) == 2:
            changes[file_attr[0]].append(file_attr[1])
    logger.info("changes -> %s", changes)
    return changes


def main(ref: str) -> None:
    """Run the script.

    :param ref: The pull request base ref
    """
    changes = list_files(ref)
    if changes:
        if is_release_pr(changes):
            logger.info("This PR looks like a release!")
            sys.exit(0)

        changelog = [x for x in changes["A"] if is_changelog_file(x)]
        logger.info("changelog files -> %s", changelog)
        if not changelog:
            if is_changelog_needed(changes):
                logger.error(
                    "Missing changelog fragment. This is not required"
                    " only if PR adds new modules and plugins or contain"
                    " only documentation changes."
                )
                sys.exit(1)
            logger.info(
                "Changelog not required as PR adds new modules and/or"
                " plugins or contain only documentation changes."
            )
        else:
            invalid_changelog_files = [
                x for x in changelog if not is_valid_changelog_format(x)
            ]
            if invalid_changelog_files:
                logger.error(
                    "The following changelog files are not valid -> %s",
                    invalid_changelog_files,
                )
                sys.exit(1)
    sys.exit(0)


def cli():
    """Entry point for the validate-changelog console script."""
    parser = argparse.ArgumentParser(
        description="Validate changelog fragments for an Ansible collection"
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Git ref to compare against (default: auto-detect from remote)",
    )

    args = parser.parse_args()
    ref = args.ref if args.ref is not None else _detect_default_ref()
    main(ref)


if __name__ == "__main__":
    cli()
