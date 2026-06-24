from pathlib import Path

from sphinx.util import logging

from .merger import (
    merge_indexes,
    write_searchindex,
)

logger = logging.getLogger(__name__)


def build_finished(app, exception):

    if exception:
        return

    if app.builder.name != "html":
        return

    projects = app.config.unified_search_projects

    if not projects:
        return

    searchindex = (
        Path(app.outdir)
        / "searchindex.js"
    )

    if not searchindex.exists():
        logger.warning(
            "No searchindex.js found"
        )
        return

    logger.info(
        "Merging %d remote indexes",
        len(projects),
    )

    merged = merge_indexes(
        searchindex,
        projects,
    )

    write_searchindex(
        searchindex,
        merged,
    )

    logger.info(
        "Unified search index written"
    )


def setup(app):

    app.add_config_value(
        "unified_search_projects",
        [],
        "html",
    )

    app.connect(
        "build-finished",
        build_finished,
    )

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }