from pathlib import Path

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util import logging

from .cache import autobuild_cache_dir
from .merger import merge_indexes, write_searchindex
from .metadata import write_project_mapping, write_search_config

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

    if app.config.unified_search_project_filter:
        context.setdefault("css_files", []).append(
            "_static/unified-search-filter.css"
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

    cache_dir = None

    if app.config.unified_search_cache_remote_indexes:
        cache_dir = autobuild_cache_dir(Path(app.doctreedir))

        logger.info(
            "[unified-search] remote index session cache: %s",
            cache_dir or "disabled (not an autobuild session)",
        )

    merged, mappings = merge_indexes(
        searchindex,
        projects,
        cache_dir=cache_dir,
    )

    write_searchindex(
        searchindex,
        merged,
    )

    write_project_mapping(
        Path(app.outdir),
        mappings,
    )

    write_search_config(
        Path(app.outdir),
        {
            "filter": bool(app.config.unified_search_project_filter),
            "local_project": (
                app.config.unified_search_local_project_name
                or app.config.project
            ),
        },
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

    app.add_config_value(
        "unified_search_cache_remote_indexes",
        False,
        "html",
        types=[bool],
    )

    app.add_config_value(
        "unified_search_project_filter",
        False,
        "html",
        types=[bool],
    )

    app.add_config_value(
        "unified_search_local_project_name",
        "",
        "html",
        types=[str],
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