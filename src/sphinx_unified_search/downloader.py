import os

import requests
from sphinx.util import logging

from .exceptions import SearchIndexError

logger = logging.getLogger(__name__)


def _build_headers(project: dict) -> dict:
    """
    Build auth headers for a project entry, if configured.

    A project can declare:
        auth_token_env: name of the environment variable holding the token
        auth_header:    header name to send the token in (default "Authorization")
        auth_scheme:    scheme prefix, e.g. "Bearer" (default "Bearer"; set to "" for none)
    """
    env_var = project.get("auth_token_env")
    if not env_var:
        return {}

    token = os.environ.get(env_var)
    if not token:
        raise SearchIndexError(
            f"[unified-search] project '{project.get('name')}' declares "
            f"auth_token_env='{env_var}' but that environment variable is "
            "not set in the build environment."
        )

    header_name = project.get("auth_header", "Authorization")
    scheme = project.get("auth_scheme", "Bearer")
    value = f"{scheme} {token}" if scheme else token

    return {header_name: value}


def download_searchindex(project: dict) -> str:
    url = project["searchindex_url"]
    headers = _build_headers(project)

    logger.info(
        "[unified-search] downloading %s",
        url,
    )

    try:
        response = requests.get(url, headers=headers, timeout=30)

        logger.info(
            "[unified-search] response status: %s",
            response.status_code,
        )

        if response.status_code in (401, 403):
            raise SearchIndexError(
                f"[unified-search] authentication failed fetching '{url}' "
                f"for project '{project.get('name')}' "
                f"(HTTP {response.status_code}). Check that the token in "
                f"'{project.get('auth_token_env')}' is valid and has read "
                "access."
            )

        response.raise_for_status()

        logger.info(
            "[unified-search] downloaded %d bytes",
            len(response.text),
        )

        return response.text

    except SearchIndexError:
        raise

    except Exception as exc:
        logger.warning(
            "[unified-search] failed to download %s: %s",
            url,
            exc,
        )
        raise
