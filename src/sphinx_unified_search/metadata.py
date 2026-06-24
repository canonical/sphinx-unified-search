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
