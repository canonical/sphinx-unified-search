from pathlib import Path

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util import logging

from .merger import merge_indexes, write_searchindex
from .metadata import write_project_mapping

logger = logging.getLogger(__name__)


def add_assets(app):
    static_dir = (
        Path(__file__).parent / "static"
    )

    if str(static_dir) not in app.config.html_static_path:
        app.config.html_static_path.append(
            str(static_dir)
        )

    logger.info(
        "[unified-search] registered static assets"
    )


def add_js_to_search_page(app, pagename, templatename, context, doctree):
    """
    Inject unified-search.js only on the search page.
    """
    if pagename != "search":
        return

    logger.info(
        "[unified-search] adding JS to search page"
    )

    if "script_files" not in context:
        return

    context["script_files"].append(
        "_static/unified-search-scorer.js"
    )

    context["script_files"].append(
        "_static/unified-search.js"
    )


def build_finished(app, exception):
    logger.info("[unified-search] build_finished() called")

    if exception:
        logger.warning(
            "[unified-search] build finished with exception: %s",
            exception,
        )
        return

    logger.info(
        "[unified-search] builder = %s",
        app.builder.name,
    )

    if not isinstance(
        app.builder,
        StandaloneHTMLBuilder,
    ):
        logger.info(
            "[unified-search] skipping: builder '%s' is not HTML-based",
            app.builder.name,
        )
        return

    projects = app.config.unified_search_projects

    logger.info(
        "[unified-search] configured projects: %s",
        projects,
    )

    if not projects:
        logger.warning(
            "[unified-search] no unified_search_projects configured"
        )
        return

    searchindex = (
        Path(app.outdir) / "searchindex.js"
    )

    logger.info(
        "[unified-search] local search index path: %s",
        searchindex,
    )

    if not searchindex.exists():
        logger.warning(
            "[unified-search] searchindex.js not found"
        )
        return

    merged, mappings = merge_indexes(
        searchindex,
        projects,
    )

    write_searchindex(
        searchindex,
        merged,
    )

    write_project_mapping(
        Path(app.outdir),
        mappings,
    )

    logger.info(
        "[unified-search] merged index contains %d documents",
        len(merged["docnames"]),
    )

    logger.info(
        "[unified-search] wrote merged search index to %s",
        searchindex,
    )


def setup(app):
    logger.info(
        "[unified-search] extension loaded"
    )

    app.add_config_value(
        "unified_search_projects",
        [],
        "html",
    )

    app.connect(
        "builder-inited",
        add_assets,
    )

    app.connect(
        "html-page-context",
        add_js_to_search_page,
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