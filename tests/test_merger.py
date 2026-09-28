import json
from pathlib import Path

import pytest

from sphinx_unified_search import merger


def _js(index: dict) -> str:
    return "Search.setIndex(" + json.dumps(index) + ")"


LOCAL = {
    "docnames": ["index", "guide"],
    "filenames": ["index.md", "guide.md"],
    "titles": ["Home", "Guide"],
    "terms": {"home": 0, "guide": [1]},
    "titleterms": {"home": 0},
    "alltitles": {"Home": [[0, None]], "Setup": [[1, "setup"]]},
    "indexentries": {"install": [[1, "install", 1]]},
    "objects": {"pkg": [[1, 0, 1, "", "func"]]},
    "objnames": {"0": ["py", "function", "Python function"]},
    "objtypes": {"0": "py:function"},
}

REMOTE = {
    "docnames": ["index", "notes"],
    "filenames": ["index.md", "notes.md"],
    "titles": ["Remote", "Release notes"],
    "terms": {"releas": [1]},
    "titleterms": {"note": 1},
    "alltitles": {
        "Setup": [[0, "setup"]],  # same heading as a local one
        "Upgrading": [[1, None]],
    },
    "indexentries": {"install": [[0, "install", 0]]},
    "objects": {
        "rpkg": [
            [1, 1, 1, "", "cls"],   # remote type 1 = py:class (new)
            [0, 0, 1, "", "fn"],    # remote type 0 = py:function (shared)
        ]
    },
    "objnames": {
        "0": ["py", "function", "Python function"],
        "1": ["py", "class", "Python class"],
    },
    "objtypes": {"0": "py:function", "1": "py:class"},
}


@pytest.fixture
def merged(tmp_path, monkeypatch):
    local = tmp_path / "searchindex.js"
    local.write_text(_js(LOCAL), encoding="utf-8")
    monkeypatch.setattr(merger, "download_searchindex", lambda r: _js(REMOTE))
    result, _ = merger.merge_indexes(
        local, [{"name": "Landscape", "base_url": "https://x"}]
    )
    return result


def test_filenames_stay_aligned_with_docnames(merged):
    assert len(merged["filenames"]) == len(merged["docnames"]) == 4
    assert merged["filenames"][2:] == ["index.md", "notes.md"]


def test_missing_remote_filenames_are_padded(tmp_path, monkeypatch):
    remote = {k: v for k, v in REMOTE.items() if k != "filenames"}
    local = tmp_path / "searchindex.js"
    local.write_text(_js(LOCAL), encoding="utf-8")
    monkeypatch.setattr(merger, "download_searchindex", lambda r: _js(remote))
    result, _ = merger.merge_indexes(local, [{"name": "L", "base_url": "x"}])
    assert result["filenames"] == ["index.md", "guide.md", "", ""]


def test_alltitles_offset_and_appended_not_replaced(merged):
    assert merged["alltitles"]["Setup"] == [[1, "setup"], [2, "setup"]]
    assert merged["alltitles"]["Upgrading"] == [[3, None]]
    assert merged["alltitles"]["Home"] == [[0, None]]  # local untouched


def test_indexentries_keep_ismain_flag(merged):
    assert merged["indexentries"]["install"] == [
        [1, "install", 1],
        [2, "install", 0],
    ]


def test_objects_remap_doc_ids_and_dedupe_types(merged):
    assert merged["objtypes"] == {"0": "py:function", "1": "py:class"}
    assert merged["objnames"]["1"] == ["py", "class", "Python class"]
    # remote type 0 (py:function) -> local 0 ; remote type 1 -> new 1
    assert merged["objects"]["rpkg"] == [[3, 1, 1, "", "cls"], [2, 0, 1, "", "fn"]]
    assert merged["objects"]["pkg"] == [[1, 0, 1, "", "func"]]


def test_terms_still_offset(merged):
    assert merged["terms"]["releas"] == [3]
    assert merged["titleterms"]["note"] == [3]
