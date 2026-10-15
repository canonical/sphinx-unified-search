from types import SimpleNamespace
from unittest.mock import Mock

import psutil
import pytest

from sphinx_unified_search import cache, extension, merger
from test_merger import LOCAL, REMOTE, _js


PROJECT = {
    "name": "Remote",
    "base_url": "https://example.com/",
    "searchindex_url": "https://example.com/searchindex.js",
}


@pytest.fixture
def download(monkeypatch):
    download = Mock(return_value=_js(REMOTE))
    monkeypatch.setattr(merger, "download_searchindex", download)
    return download


def merge(tmp_path, projects, cache_dir):
    local = tmp_path / "searchindex.js"
    local.write_text(_js(LOCAL), encoding="utf-8")
    return merger.merge_indexes(local, projects, cache_dir=cache_dir)


def test_default_downloads_every_build(tmp_path, download):
    merge(tmp_path, [PROJECT], None)
    merge(tmp_path, [PROJECT], None)
    assert download.call_count == 2


def test_session_cache_preserves_merge_and_mapping(tmp_path, download):
    cache_dir = tmp_path / "cache"
    first = merge(tmp_path, [PROJECT], cache_dir)
    second = merge(tmp_path, [PROJECT], cache_dir)
    assert download.call_count == 1
    assert first == second
    assert len(second[0]["docnames"]) == 4


def test_new_session_downloads_again(tmp_path, download):
    merge(tmp_path, [PROJECT], tmp_path / "session-1")
    merge(tmp_path, [PROJECT], tmp_path / "session-2")
    assert download.call_count == 2


def test_project_mapping_changes_do_not_refetch(tmp_path, download):
    cache_dir = tmp_path / "cache"
    merge(tmp_path, [PROJECT], cache_dir)
    changed = dict(PROJECT, name="Renamed", base_url="https://new.example.com/")
    _, mapping = merge(tmp_path, [changed], cache_dir)
    assert download.call_count == 1
    assert mapping["__unified__/renamed/index"]["base_url"] == changed["base_url"]


def test_url_changes_and_multiple_projects_fetch_separately(tmp_path, download):
    other = dict(PROJECT, name="Other", searchindex_url="https://other/index.js")
    for _ in range(2):
        merge(tmp_path, [PROJECT, other], tmp_path / "cache")
    assert download.call_count == 2


@pytest.mark.parametrize("setting", ["auth_scheme", "auth_header", "token"])
def test_authentication_changes_refetch(tmp_path, monkeypatch, download, setting):
    project = dict(PROJECT, auth_token_env="DOCS_TOKEN")
    monkeypatch.setenv("DOCS_TOKEN", "first-secret")
    merge(tmp_path, [project], tmp_path / "cache")
    if setting == "token":
        monkeypatch.setenv("DOCS_TOKEN", "second-secret")
    else:
        project[setting] = "Different"
    merge(tmp_path, [project], tmp_path / "cache")
    assert download.call_count == 2
    for path in (tmp_path / "cache").iterdir():
        assert "secret" not in path.name
        assert "secret" not in path.read_text()


def test_missing_authentication_is_not_bypassed_by_cache(
    tmp_path, monkeypatch, download
):
    project = dict(PROJECT, auth_token_env="DOCS_TOKEN")
    monkeypatch.setenv("DOCS_TOKEN", "secret")
    merge(tmp_path, [project], tmp_path / "cache")
    monkeypatch.delenv("DOCS_TOKEN")
    with pytest.raises(merger.SearchIndexError, match="not set"):
        merge(tmp_path, [project], tmp_path / "cache")


@pytest.mark.parametrize("failure", [OSError("unavailable"), "not an index"])
def test_failed_downloads_and_invalid_indexes_are_retried(
    tmp_path, download, failure
):
    download.side_effect = [failure, _js(REMOTE)]
    first, _ = merge(tmp_path, [PROJECT], tmp_path / "cache")
    second, _ = merge(tmp_path, [PROJECT], tmp_path / "cache")
    third, _ = merge(tmp_path, [PROJECT], tmp_path / "cache")
    assert first["docnames"] == LOCAL["docnames"]
    assert len(second["docnames"]) == len(third["docnames"]) == 4
    assert download.call_count == 2


def test_autobuild_process_identity_scopes_cache(tmp_path, monkeypatch):
    parent = Mock(pid=123)
    parent.cmdline.return_value = ["python", "-m", "sphinx_autobuild", "docs"]
    parent.create_time.return_value = 1.0
    child = Mock()
    child.cmdline.return_value = ["python", "-m", "sphinx", "build"]
    child.parent.return_value = parent
    monkeypatch.setattr(cache.psutil, "Process", lambda: child)
    first = cache.autobuild_cache_dir(tmp_path)
    assert first.parent == tmp_path / "unified-search-cache"
    assert cache.autobuild_cache_dir(tmp_path) == first
    parent.create_time.return_value = 2.0
    assert cache.autobuild_cache_dir(tmp_path) != first


@pytest.mark.parametrize(
    "command",
    [
        ["/venv/bin/sphinx-autobuild", "docs"],
        [r"C:/venv/Scripts/sphinx-autobuild.exe", "docs"],
        ["python", "-m", "sphinx_autobuild", "docs"],
    ],
)
def test_in_process_autobuild(tmp_path, monkeypatch, command):
    process = Mock(pid=123)
    process.cmdline.return_value = command
    process.create_time.return_value = 1.0
    monkeypatch.setattr(cache.psutil, "Process", lambda: process)
    assert cache.autobuild_cache_dir(tmp_path) is not None


def test_normal_sphinx_build_has_no_session_cache(tmp_path, monkeypatch):
    process = Mock()
    process.cmdline.return_value = ["python", "-m", "sphinx", "sphinx-autobuild"]
    process.parent.return_value = None
    monkeypatch.setattr(cache.psutil, "Process", lambda: process)
    assert cache.autobuild_cache_dir(tmp_path) is None


@pytest.mark.parametrize("required", [True, False])
def test_authentication_failures_preserve_required_behavior(
    tmp_path, download, required
):
    project = dict(PROJECT, required=required)
    download.side_effect = [merger.SearchIndexError("authentication failed"), _js(REMOTE)]
    if required:
        with pytest.raises(merger.SearchIndexError, match="authentication failed"):
            merge(tmp_path, [project], tmp_path / "cache")
    else:
        result, _ = merge(tmp_path, [project], tmp_path / "cache")
        assert result["docnames"] == LOCAL["docnames"]
    result, _ = merge(tmp_path, [project], tmp_path / "cache")
    assert len(result["docnames"]) == 4
    assert download.call_count == 2


def test_uninspectable_process_warns_and_disables_cache(
    tmp_path, monkeypatch, caplog
):
    process = Mock()
    process.cmdline.side_effect = psutil.AccessDenied(pid=123)
    monkeypatch.setattr(cache.psutil, "Process", lambda: process)
    assert cache.autobuild_cache_dir(tmp_path) is None
    assert "cannot identify autobuild session" in caplog.text


def test_cache_config_is_opt_in():
    app = Mock()
    extension.setup(app)
    app.add_config_value.assert_any_call(
        "unified_search_cache_remote_indexes", False, "html", types=[bool]
    )


@pytest.mark.parametrize("enabled", [False, True])
def test_build_finished_wires_session_cache(tmp_path, monkeypatch, enabled):
    app = SimpleNamespace(
        builder=Mock(spec=extension.StandaloneHTMLBuilder),
        config=SimpleNamespace(
            unified_search_projects=[PROJECT],
            unified_search_cache_remote_indexes=enabled,
        ),
        outdir=tmp_path,
        doctreedir=tmp_path / "doctrees",
    )
    (tmp_path / "searchindex.js").write_text(_js(LOCAL), encoding="utf-8")
    session = Mock(return_value=tmp_path / "cache")
    merge_indexes = Mock(return_value=(LOCAL, {}))
    monkeypatch.setattr(extension, "autobuild_cache_dir", session)
    monkeypatch.setattr(extension, "merge_indexes", merge_indexes)
    extension.build_finished(app, None)
    merge_indexes.assert_called_once_with(
        tmp_path / "searchindex.js",
        [PROJECT],
        cache_dir=tmp_path / "cache" if enabled else None,
    )
    assert session.call_count == int(enabled)
