import json
from pathlib import Path

from sphinx.util import logging

logger = logging.getLogger(__name__)


def write_project_mapping(
    output_dir: Path,
    mappings: dict,
):
    path = (
        output_dir
        / "_static"
        / "unified_search_projects.json"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(mappings),
        encoding="utf-8",
    )

    logger.info(
        "[unified-search] wrote project mapping to %s",
        path,
    )


def write_search_config(
    output_dir: Path,
    config: dict,
):
    """
    Write the client-side settings (e.g. whether to show the project
    filter) next to the project mapping, for unified-search.js to read.
    """
    path = (
        output_dir
        / "_static"
        / "unified_search_config.json"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    logger.info(
        "[unified-search] wrote search config to %s",
        path,
    )
