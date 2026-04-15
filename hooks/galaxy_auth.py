"""Shared helpers for configuring additional Galaxy server authentication.

Provides argparse arguments and an environment setup function that hooks
can use to inject ANSIBLE_GALAXY_SERVER_* env vars before spawning
subprocesses.  This lets collections with certified/private dependencies
authenticate to Automation Hub (or any private Galaxy server) without
creating temporary ansible.cfg files.

Example pre-commit config usage::

    - repo: https://github.com/ansible/ansible-content-prek-actions
      hooks:
        - id: sanity
          args:
            - --galaxy-server-url=https://console.redhat.com/api/automation-hub/content/published/
            - --galaxy-server-auth-url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
            - --galaxy-server-token-env=AH_TOKEN
"""

from __future__ import annotations

import argparse
import os


def add_galaxy_server_args(parser: argparse.ArgumentParser) -> None:
    """Register --galaxy-server-* CLI flags on *parser*."""
    group = parser.add_argument_group(
        "Galaxy server authentication",
        "Configure an additional Galaxy server (e.g. Automation Hub) that is "
        "searched before the default Galaxy server.",
    )
    group.add_argument(
        "--galaxy-server-url",
        default=None,
        help="URL of the additional Galaxy server.",
    )
    group.add_argument(
        "--galaxy-server-auth-url",
        default=None,
        help="SSO / token endpoint for the additional Galaxy server.",
    )
    group.add_argument(
        "--galaxy-server-token",
        default=None,
        help=(
            "Auth token value.  Prefer --galaxy-server-token-env to avoid "
            "placing secrets in config files."
        ),
    )
    group.add_argument(
        "--galaxy-server-token-env",
        default=None,
        help=(
            "Name of an environment variable that contains the auth token "
            "(e.g. AH_TOKEN).  This is safer than --galaxy-server-token."
        ),
    )


def apply_galaxy_server_env(args: argparse.Namespace) -> None:
    """Set ANSIBLE_GALAXY_SERVER_* env vars based on parsed *args*.

    Does nothing when ``--galaxy-server-url`` was not provided.
    """
    url = args.galaxy_server_url
    if not url:
        return

    token = args.galaxy_server_token
    if not token and args.galaxy_server_token_env:
        token = os.environ.get(args.galaxy_server_token_env, "")

    os.environ["ANSIBLE_GALAXY_SERVER_LIST"] = "certified,galaxy"
    os.environ["ANSIBLE_GALAXY_SERVER_CERTIFIED_URL"] = url
    os.environ["ANSIBLE_GALAXY_SERVER_GALAXY_URL"] = "https://galaxy.ansible.com/api/"

    if token:
        os.environ["ANSIBLE_GALAXY_SERVER_CERTIFIED_TOKEN"] = token
    if args.galaxy_server_auth_url:
        os.environ["ANSIBLE_GALAXY_SERVER_CERTIFIED_AUTH_URL"] = (
            args.galaxy_server_auth_url
        )
