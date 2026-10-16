import json
from types import SimpleNamespace
from unittest.mock import Mock

from sphinx.builders.html import StandaloneHTMLBuilder

from sphinx_unified_search import extension
from sphinx_unified_search.metadata import write_search_config


def _app(tmp_path, **config):
    builder = Mock(spec=StandaloneHTMLBuilder)
    builder.name = "html"
    defaults = {
        "unified_search_projects": [{"name": "R"}],
        "unified_search_cache_remote_indexes": False,
        "unified_search_project_filter": False,
        "unified_search_local_project_name": "",
        "project": "Sphinx Project",
    }
    defaults.update(config)
    return SimpleNamespace(
        config=SimpleNamespace(**defaults),
        outdir=str(tmp_path),
        doctreedir=str(tmp_path / "doctrees"),
        builder=builder,
    )


def test_write_search_config(tmp_path):
    write_search_config(tmp_path, {"filter": True, "local_project": "Docs"})
    path = tmp_path / "_static" / "unified_search_config.json"
    assert json.loads(path.read_text()) == {"filter": True, "local_project": "Docs"}


def test_options_registered_with_safe_defaults():
    app = Mock()
    extension.setup(app)
    registered = {c.args[0]: c.args[1] for c in app.add_config_value.call_args_list}
    assert registered["unified_search_project_filter"] is False
    assert registered["unified_search_local_project_name"] == ""


def _run_build_finished(monkeypatch, tmp_path, **config):
    (tmp_path / "searchindex.js").write_text("x")
    monkeypatch.setattr(
        extension, "merge_indexes", lambda *a, **k: ({"docnames": []}, {})
    )
    monkeypatch.setattr(extension, "write_searchindex", lambda *a, **k: None)
    extension.build_finished(_app(tmp_path, **config), None)
    path = tmp_path / "_static" / "unified_search_config.json"
    return json.loads(path.read_text())


def test_build_finished_filter_off_by_default(monkeypatch, tmp_path):
    cfg = _run_build_finished(monkeypatch, tmp_path)
    assert cfg == {"filter": False, "local_project": "Sphinx Project"}


def test_build_finished_filter_on_with_custom_local_name(monkeypatch, tmp_path):
    cfg = _run_build_finished(
        monkeypatch,
        tmp_path,
        unified_search_project_filter=True,
        unified_search_local_project_name="My Docs",
    )
    assert cfg == {"filter": True, "local_project": "My Docs"}


def _page_context(flag):
    app = SimpleNamespace(
        config=SimpleNamespace(unified_search_project_filter=flag)
    )
    ctx = {"script_files": [], "css_files": []}
    extension.add_js_to_search_page(app, "search", "search.html", ctx, None)
    return ctx


def test_css_added_to_search_page_only_when_filter_enabled():
    assert "_static/unified-search-filter.css" in _page_context(True)["css_files"]
    assert _page_context(False)["css_files"] == []
